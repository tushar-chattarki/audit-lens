"""
ai_layer.py
===========
Member 6 (Om) — AI Layer for Banking FS Review Audit Copilot
Hackathon: Cognizant Technoverse — Banking Track

Local LLM Engine: Ollama (e.g. llama3.2, mistral, llama3, qwen2.5, etc.)
No external API keys or third-party cloud SDKs required.

Inputs:
    canonical_json  : dict  — Tushar's extraction output (schema v1.0)
    findings        : list  — Merged findings from Yogeshwari (math) + Parth (consistency/PY)

Outputs:
    list of Finding objects (same shape as input findings) with ai_explanation populated
    + grammar findings
    + one overall summary finding

Rules (strictly enforced):
    - NEVER send raw documents to the LLM for numeric work
    - NEVER let the LLM invent a number not present in canonical_json
    - ALWAYS label explanations as "SUGGESTED — pending reviewer sign-off"
    - ALWAYS return valid JSON even if Ollama fails (ai_explanation = null)
    - NEVER let an LLM failure crash the pipeline
"""

import os
import json
import uuid
import re
import urllib.request
import urllib.error

# ── Local Ollama Configuration ────────────────────────────────────────────────
# Defaults to localhost Ollama instance with llama3.2, customizable via environment variables
OLLAMA_HOST  = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:latest")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "60"))


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — shared across all three sub-tasks
# Master instruction governing the LLM's behaviour in every call.
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """
You are an AI assistant embedded inside a banking financial-statement review tool.
Your role is to assist a human auditor by explaining anomalies, reviewing language,
and summarising findings. You operate under strict rules:

ABSOLUTE RULES — never break these:
1. You ONLY use figures that are explicitly present in the JSON data provided to you.
   Never calculate, estimate, or invent any number. If a figure is not in the input, say so.
2. Every explanation you produce is a SUGGESTED CANDIDATE for reviewer consideration.
   Always include the label: "SUGGESTED — pending reviewer sign-off"
3. Never assert a cause as fact. Use language like:
   "likely driven by", "consistent with", "suggests", "reviewer to confirm".
4. Always output valid JSON that exactly matches the schema requested.
   No markdown formatting, no preamble, no trailing commentary — pure JSON only.
5. Never reproduce the full input data in your output.
6. If you cannot explain something from the data given, set confidence = "low"
   and state what additional information the reviewer needs.

Your output must always be valid JSON parseable by json.loads().
"""


# ═══════════════════════════════════════════════════════════════════════════════
# OLLAMA CLIENT HELPER — Zero-dependency HTTP caller using standard urllib
# ═══════════════════════════════════════════════════════════════════════════════

def call_ollama(system_prompt: str, user_prompt: str, model: str = OLLAMA_MODEL, host: str = OLLAMA_HOST) -> dict:
    """
    Calls local Ollama chat completion endpoint (/api/chat) with JSON format constraint.
    Returns parsed dictionary or raises an exception.
    """
    url = f"{host}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for deterministic & grounded output
            "top_p": 0.9,
        }
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as response:
            resp_body = response.read().decode("utf-8")
            resp_json = json.loads(resp_body)
            raw_text = resp_json.get("message", {}).get("content", "").strip()

            # Handle edge cases where models might wrap JSON inside markdown blocks
            cleaned_text = re.sub(r"^```json\s*", "", raw_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r"^```\s*", "", cleaned_text)
            cleaned_text = re.sub(r"\s*```$", "", cleaned_text).strip()

            return json.loads(cleaned_text)

    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not connect to Ollama at {host}. Is Ollama running? Error: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Ollama returned non-JSON response: '{raw_text[:200]}...'. Error: {e}")
    except Exception as e:
        raise RuntimeError(f"Ollama request error: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# SUB-TASK 1 — GRAMMAR REVIEW
# Input  : narrative text extracted from notes/disclosures
# Output : finding object for each flagged issue
# ═══════════════════════════════════════════════════════════════════════════════

GRAMMAR_USER_PROMPT = """
You are reviewing the narrative disclosure text from a bank's financial statements.
Your job is to check for spelling errors, grammatical issues, and unclear phrasing
that a professional auditor would want corrected before sign-off.

BANK: {bank_name}
PERIOD: {period}
UNIT: {unit} ({currency})

NARRATIVE TEXT TO REVIEW:
Note reference : {note_ref}
Source page    : {page}
Text           : "{narrative_text}"

TASK:
1. Identify any spelling errors, typos, grammatical mistakes, or unclear disclosures.
2. If the text is completely clear and correct, set status to "pass".
3. If issues are found, set status to "exception" and suggest a corrected version.
4. Only reference figures already present in the text or in the canonical data snippet below.

CANONICAL DATA SNIPPET (for context — do not invent new numbers):
{canonical_snippet}

Return ONLY this JSON object, no other text:
{{
  "status": "pass" or "exception",
  "flagged_issue": "describe the specific problem or typo, or null if pass",
  "original_text": "exact original text",
  "suggested_revision": "your improved version, or null if pass",
  "confidence": "high" or "medium" or "low",
  "caveats": "what the reviewer should verify before adopting the revision"
}}
"""


def run_grammar_review(canonical_json: dict) -> list[dict]:
    """
    Scans note narratives in canonical JSON for spelling/grammar/phrasing issues.
    Returns a list of Finding objects conforming to the system contract.
    """
    findings = []
    notes = canonical_json.get("statements", {}).get("notes", {})
    bank_name = canonical_json.get("bank_name", "Unknown Bank")
    currency  = canonical_json.get("currency", "INR")
    unit      = canonical_json.get("unit", "crore")
    period    = canonical_json.get("periods", ["FY2025"])[0]

    for note_key, note_data in notes.items():
        if not isinstance(note_data, dict):
            continue

        narrative = note_data.get("narrative")
        if not narrative or not narrative.get("text"):
            continue

        narrative_text = narrative["text"]
        evidence       = narrative.get("evidence", {})
        page           = evidence.get("page", "unknown")

        canonical_snippet = {}
        for period_key in canonical_json.get("periods", []):
            if period_key in note_data and isinstance(note_data[period_key], dict):
                canonical_snippet[period_key] = note_data[period_key].get("value")

        user_prompt = GRAMMAR_USER_PROMPT.format(
            bank_name        = bank_name,
            period           = period,
            unit             = unit,
            currency         = currency,
            note_ref         = note_key,
            page             = page,
            narrative_text   = narrative_text,
            canonical_snippet= json.dumps(canonical_snippet, indent=2),
        )

        try:
            data = call_ollama(SYSTEM_PROMPT, user_prompt)

            is_exception = str(data.get("status", "")).lower() == "exception"
            finding = {
                "finding_id"   : f"F-AI-GRAM-{str(uuid.uuid4())[:8].upper()}",
                "module"       : "ai_layer",
                "check"        : "grammar_review",
                "status"       : "exception" if is_exception else "pass",
                "severity"     : "low" if is_exception else None,
                "expected"     : "Correct spelling and grammar in narrative disclosures",
                "actual"       : data.get("flagged_issue") if is_exception else "Clean narrative with no grammar issues",
                "difference"   : None,
                "evidence"     : [evidence] if evidence else [],
                "ai_explanation": {
                    "original_text"      : data.get("original_text", narrative_text),
                    "flagged_issue"      : data.get("flagged_issue"),
                    "suggested_revision" : data.get("suggested_revision"),
                    "confidence"         : data.get("confidence", "medium"),
                    "caveats"            : data.get("caveats"),
                    "wp514_target_field" : "ai_explanation",
                    "label"              : "SUGGESTED — pending reviewer sign-off",
                } if is_exception else None,
            }
            findings.append(finding)

        except Exception as e:
            # Fallback: keep pipeline alive with structured not_applicable finding
            findings.append({
                "finding_id"    : f"F-AI-GRAM-{str(uuid.uuid4())[:8].upper()}",
                "module"        : "ai_layer",
                "check"         : "grammar_review",
                "status"        : "not_applicable",
                "severity"      : None,
                "expected"      : "Correct spelling and grammar in narrative disclosures",
                "actual"        : None,
                "difference"    : None,
                "evidence"      : [evidence] if evidence else [],
                "ai_explanation": None,
                "_error"        : f"Ollama unavailable: {str(e)}",
            })

    return findings


# ═══════════════════════════════════════════════════════════════════════════════
# SUB-TASK 2 — ANOMALY EXPLANATION
# Input  : exception findings from Math / Consistency engines + canonical JSON
# Output : enriched findings with grounded ai_explanation populated
# ═══════════════════════════════════════════════════════════════════════════════

ANOMALY_USER_PROMPT = """
You are reviewing a flagged exception from a bank's financial statement review.
Your job is to produce a grounded, evidence-based candidate explanation for the anomaly.

BANK: {bank_name}
PERIOD: {period}
UNIT: All figures below are in {unit} ({currency})

EXCEPTION DETAILS (from the deterministic review engine):
  Finding ID    : {finding_id}
  Check         : {check}
  Statement     : {statement}
  Line item     : {line_item}
  Expected      : {expected}
  Actual        : {actual}
  Difference    : {difference}
  Prior year    : {prior_year_value}
  % change      : {pct_change}

CANONICAL DATA — the only figures you may reference (do not use any other numbers):
{canonical_data}

NOTE NARRATIVES — the only text evidence available:
{note_narratives}

TASK:
Write a concise, plain-English explanation of why this anomaly may have occurred.
- Only use figures from CANONICAL DATA above.
- Only reference disclosures from NOTE NARRATIVES above.
- If note narratives explain the movement (e.g., one-off sale, reclassification), cite them directly.
- If they do not, state that no explanatory disclosure was located and mention what the reviewer needs to verify.
- Use hedging language: "likely driven by", "consistent with", "suggests", "reviewer to confirm".
- If the anomaly is a cash mismatch with no note explanation, say confidence is low.
- State whether the item appears recurring or non-recurring based only on the notes.

Return ONLY this JSON, no other text:
{{
  "text": "your full explanation paragraph",
  "confidence": "high" or "medium" or "low",
  "caveats": "what the reviewer must verify to confirm or reject this explanation",
  "recurring": true or false or null,
  "wp514_target_field": "ai_explanation",
  "label": "SUGGESTED — pending reviewer sign-off"
}}
"""


def run_anomaly_explanation(canonical_json: dict, findings: list[dict]) -> list[dict]:
    """
    For each exception finding from Math/Consistency engines, calls Ollama to produce
    a grounded candidate explanation. Returns the enriched findings list.
    """
    enriched = []
    bank_name = canonical_json.get("bank_name", "Unknown Bank")
    currency  = canonical_json.get("currency", "INR")
    unit      = canonical_json.get("unit", "crore")
    periods   = canonical_json.get("periods", [])

    # Build note-narratives lookup once
    note_narratives = {}
    notes_dict = canonical_json.get("statements", {}).get("notes", {})
    if isinstance(notes_dict, dict):
        for note_key, note_data in notes_dict.items():
            if isinstance(note_data, dict) and "narrative" in note_data and note_data["narrative"].get("text"):
                note_narratives[note_key] = note_data["narrative"]["text"]

    for finding in findings:
        # Only exceptions need explanatory narrative; passes flow through unchanged
        if finding.get("status") != "exception":
            enriched.append(finding)
            continue

        evidence_list = finding.get("evidence", [])
        period = periods[0] if periods else "FY2025"

        # Extract relevant figures from evidence pointers to ground the LLM
        canonical_slice = {}
        for ev in evidence_list:
            row   = ev.get("row", "")
            tbl   = ev.get("table", "")
            p     = ev.get("period", period)
            key   = f"{tbl} > {row} > {p}"
            for stmt_name, stmt_data in canonical_json.get("statements", {}).items():
                found_val = _find_value_in_statement(stmt_data, row, p)
                if found_val is not None:
                    canonical_slice[key] = found_val
                    break

        # Also add note values
        for note_key, note_data in notes_dict.items():
            if isinstance(note_data, dict):
                for p_key in periods:
                    if isinstance(note_data.get(p_key), dict):
                        canonical_slice[f"{note_key} > {p_key}"] = note_data[p_key].get("value")

        user_prompt = ANOMALY_USER_PROMPT.format(
            bank_name         = bank_name,
            period            = period,
            unit              = unit,
            currency          = currency,
            finding_id        = finding.get("finding_id", "unknown"),
            check             = finding.get("check", "unknown"),
            statement         = finding.get("statement", "unknown"),
            line_item         = finding.get("line_item", finding.get("check", "unknown")),
            expected          = finding.get("expected", "N/A"),
            actual            = finding.get("actual", "N/A"),
            difference        = finding.get("difference", "N/A"),
            prior_year_value  = finding.get("prior_year_value", "N/A"),
            pct_change        = finding.get("pct_change", "N/A"),
            canonical_data    = json.dumps(canonical_slice, indent=2),
            note_narratives   = json.dumps(note_narratives, indent=2),
        )

        try:
            data = call_ollama(SYSTEM_PROMPT, user_prompt)
            finding["ai_explanation"] = {
                "text"               : data.get("text"),
                "confidence"         : data.get("confidence", "medium"),
                "caveats"            : data.get("caveats"),
                "recurring"          : data.get("recurring"),
                "wp514_target_field" : "ai_explanation",
                "label"              : "SUGGESTED — pending reviewer sign-off",
                "source_finding_id"  : finding.get("finding_id"),
            }
        except Exception as e:
            finding["ai_explanation"] = None
            finding["_ai_error"]      = f"Ollama unavailable: {str(e)}"

        enriched.append(finding)

    return enriched


# ═══════════════════════════════════════════════════════════════════════════════
# SUB-TASK 3 — OVERALL REVIEW SUMMARY
# Input  : Full merged findings list (all modules)
# Output : One Finding object with check="overall_review_summary"
# ═══════════════════════════════════════════════════════════════════════════════

SUMMARY_USER_PROMPT = """
You are an AI assistant helping an auditor prepare a WP-514 working paper.
Write a plain-English overall review summary for the reviewer based ONLY
on the validated findings list provided below.

BANK: {bank_name}
PERIOD: {period}
UNIT: {unit} ({currency})

VALIDATED FINDINGS LIST (these are the only facts you may use):
{findings_summary}

COUNTS (use these exact numbers — do not recount yourself):
  Total findings   : {total}
  High severity    : {high}
  Medium severity  : {medium}
  Low severity     : {low}
  Passes           : {passes}
  Exceptions       : {exceptions}

TASK:
Write one concise paragraph (4–6 sentences) that:
1. States the overall review status (pass or number of exceptions found) with exact counts.
2. Highlights each high-severity exception (e.g. balance sheet mismatch or material variance) and its audit implication.
3. Briefly references medium/low findings.
4. Concludes by explicitly stating that all AI explanations are candidate suggestions requiring human reviewer sign-off.

Rules:
- Only reference items from the VALIDATED FINDINGS LIST above.
- Do not invent numbers or analyses beyond what the findings state.
- Write professionally for a senior auditor signing the WP-514 working paper.

Return ONLY this JSON, no other text:
{{
  "text": "your full summary paragraph",
  "label": "AI-GENERATED SUMMARY — for reviewer reference only"
}}
"""


def run_overall_summary(canonical_json: dict, all_findings: list[dict]) -> dict:
    """
    Produces a single overall review summary finding for WP-514 Section 8.
    Receives the full merged findings list (math + consistency + PY + AI grammar + anomaly).
    """
    bank_name = canonical_json.get("bank_name", "Unknown Bank")
    currency  = canonical_json.get("currency", "INR")
    unit      = canonical_json.get("unit", "crore")
    period    = canonical_json.get("periods", ["FY2025"])[0]

    # Deterministic severity counts — never delegated to the LLM
    counts = {"high": 0, "medium": 0, "low": 0, "passes": 0, "exceptions": 0}
    for f in all_findings:
        if f.get("status") == "pass":
            counts["passes"] += 1
        elif f.get("status") == "exception":
            counts["exceptions"] += 1
            sev = f.get("severity", "low")
            if sev in counts:
                counts[sev] += 1

    findings_summary_lines = []
    for f in all_findings:
        if f.get("status") == "exception":
            sev   = str(f.get("severity", "low")).upper()
            check = f.get("check", "unknown")
            fid   = f.get("finding_id", "")
            diff  = f.get("difference")
            diff_str = f" (difference: {diff} {unit})" if diff is not None else ""
            exp_txt = ""
            if f.get("ai_explanation") and isinstance(f["ai_explanation"], dict) and f["ai_explanation"].get("text"):
                exp_txt = " | AI note: " + f["ai_explanation"]["text"][:120] + "..."
            findings_summary_lines.append(
                f"[{sev}] {fid} · {check}{diff_str}{exp_txt}"
            )

    findings_summary = "\n".join(findings_summary_lines) if findings_summary_lines else "No exceptions found across statements."

    user_prompt = SUMMARY_USER_PROMPT.format(
        bank_name       = bank_name,
        period          = period,
        unit            = unit,
        currency        = currency,
        findings_summary= findings_summary,
        total           = len(all_findings),
        high            = counts["high"],
        medium          = counts["medium"],
        low             = counts["low"],
        passes          = counts["passes"],
        exceptions      = counts["exceptions"],
    )

    try:
        data = call_ollama(SYSTEM_PROMPT, user_prompt)
        return {
            "finding_id"    : f"F-AI-SUM-{str(uuid.uuid4())[:8].upper()}",
            "module"        : "ai_layer",
            "check"         : "overall_review_summary",
            "status"        : "pass",
            "severity"      : None,
            "expected"      : "Comprehensive review summary generated",
            "actual"        : "Summary prepared for reviewer sign-off",
            "difference"    : None,
            "evidence"      : [],
            "ai_explanation": {
                "text"               : data.get("text"),
                "confidence"         : "high",
                "caveats"            : "Reviewer must confirm all underlying check findings before final sign-off.",
                "wp514_target_field" : "review_summary",
                "label"              : "AI-GENERATED SUMMARY — for reviewer reference only",
            },
        }

    except Exception as e:
        return {
            "finding_id"    : f"F-AI-SUM-{str(uuid.uuid4())[:8].upper()}",
            "module"        : "ai_layer",
            "check"         : "overall_review_summary",
            "status"        : "not_applicable",
            "severity"      : None,
            "expected"      : None,
            "actual"        : None,
            "difference"    : None,
            "evidence"      : [],
            "ai_explanation": None,
            "_error"        : f"Ollama unavailable: {str(e)}",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT — Orchestrator integration (Member 7 / FastAPI)
# ═══════════════════════════════════════════════════════════════════════════════

def run(canonical_json: dict, findings: list[dict]) -> dict:
    """
    Main function called by the orchestrator after math + consistency engines finish.

    Args:
        canonical_json : Tushar's canonical JSON output (schema v1.0)
        findings       : Merged list from Yogeshwari (math) + Parth (consistency/PY)

    Returns:
        dict containing:
            "findings"       : enriched findings list (all modules)
            "overall_status" : summary counts
            "wp514_field_map": lookup for WP-514 module
            "ai_layer_status": "completed" or "partial"
    """
    print(f"[AI Layer - Ollama ({OLLAMA_MODEL})] Starting. Received {len(findings)} findings from engines.")

    # ── Step 1: Grammar review (runs on note narratives)
    print("[AI Layer] Running grammar review on note narratives...")
    grammar_findings = run_grammar_review(canonical_json)
    print(f"[AI Layer] Grammar check finished: {len(grammar_findings)} items processed.")

    # ── Step 2: Anomaly explanation (enriches exception findings)
    print("[AI Layer] Running grounded anomaly explanations...")
    enriched_findings = run_anomaly_explanation(canonical_json, findings)
    print(f"[AI Layer] Anomaly explanation finished: {len(enriched_findings)} findings enriched.")

    # ── Step 3: Merge all findings
    all_findings = enriched_findings + grammar_findings

    # ── Step 4: Overall review summary
    print("[AI Layer] Generating overall review summary...")
    summary_finding = run_overall_summary(canonical_json, all_findings)
    all_findings.append(summary_finding)
    print("[AI Layer] Summary generation completed.")

    # ── Step 5: Build overall_status counts (deterministic)
    overall_status = _build_overall_status(all_findings)

    # ── Step 6: Build wp514_field_map for WP-514 module
    wp514_field_map = _build_wp514_map(all_findings)

    # ── Step 7: Check if any call fell back to null
    has_errors = any(f.get("_ai_error") or f.get("_error") for f in all_findings)
    ai_status  = "partial" if has_errors else "completed"

    print(f"[AI Layer] Finished successfully. Status: {ai_status}. Total findings: {len(all_findings)}.")

    return {
        "job_id"          : canonical_json.get("job_id"),
        "bank_id"         : canonical_json.get("bank_id"),
        "bank_name"       : canonical_json.get("bank_name"),
        "currency"        : canonical_json.get("currency"),
        "unit"            : canonical_json.get("unit"),
        "periods"         : canonical_json.get("periods"),
        "ai_layer_version": "1.0",
        "llm_engine"      : f"ollama/{OLLAMA_MODEL}",
        "ai_layer_status" : ai_status,
        "findings"        : all_findings,
        "overall_status"  : overall_status,
        "wp514_field_map" : wp514_field_map,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _find_value_in_statement(stmt_data: dict, row_label: str, period: str):
    """
    Recursively walks a statement dict to find a value matching
    a row label and period. Returns the numeric value or None.
    """
    if isinstance(stmt_data, dict):
        for key, val in stmt_data.items():
            if isinstance(val, dict):
                if period in val and isinstance(val[period], dict):
                    ev = val[period].get("evidence", {})
                    if ev.get("row", "").lower() == row_label.lower():
                        return val[period].get("value")
                result = _find_value_in_statement(val, row_label, period)
                if result is not None:
                    return result
    return None


def _build_overall_status(all_findings: list[dict]) -> dict:
    """Deterministic counts — never computed by LLM."""
    counts = {
        "result"        : "pass",
        "total_findings": len(all_findings),
        "exceptions"    : 0,
        "passes"        : 0,
        "by_severity"   : {"high": 0, "medium": 0, "low": 0, "info": 0},
        "by_module_check": {},
    }
    for f in all_findings:
        check = f.get("check", "unknown")
        counts["by_module_check"][check] = counts["by_module_check"].get(check, 0) + 1
        if f.get("status") == "exception":
            counts["exceptions"] += 1
            counts["result"]      = "exceptions_found"
            sev = f.get("severity") or "info"
            if sev in counts["by_severity"]:
                counts["by_severity"][sev] += 1
        elif f.get("status") == "pass":
            counts["passes"] += 1
    return counts


def _build_wp514_map(all_findings: list[dict]) -> dict:
    """
    Builds the lookup table for the WP-514 module to map
    findings to working paper sections and target fields.
    """
    section_map = {
        "grammar_review"            : {"section": 3, "field": "ai_explanation"},
        "anomaly_explanation"       : {"section": 3, "field": "ai_explanation"},
        "prior_year_movement"       : {"section": 5, "field": "reason_for_flag"},
        "prior_year_reason_for_flag": {"section": 5, "field": "reason_for_flag"},
        "analytics_explanation"     : {"section": 6, "field": "explanation"},
        "overall_review_summary"    : {"section": 8, "field": "review_summary"},
    }
    wp_map = {}
    for f in all_findings:
        fid   = f.get("finding_id")
        check = f.get("check", "")
        if fid and check in section_map:
            wp_map[fid] = {
                **section_map[check],
                "row_label": f.get("check", ""),
            }
    return wp_map


# ═══════════════════════════════════════════════════════════════════════════════
# LOCAL TEST SUITE (GreenPeak Bank Walkthrough Case)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"=== TESTING AI LAYER WITH LOCAL OLLAMA ({OLLAMA_MODEL}) ===")

    sample_canonical = {
        "schema_version": "1.0",
        "job_id"        : "JOB-001",
        "bank_id"       : "GREENPEAK",
        "bank_name"     : "GreenPeak Bank Ltd.",
        "currency"      : "INR",
        "unit"          : "crore",
        "periods"       : ["FY2025", "FY2024"],
        "statements": {
            "balance_sheet": {
                "total_assets": {
                    "FY2025": {"value": 12450.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Total Assets", "period": "FY2025"}},
                    "FY2024": {"value": 11020.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Total Assets", "period": "FY2024"}}
                }
            },
            "profit_and_loss": {
                "income": {
                    "other_income": {
                        "FY2025": {"value": 185.0, "evidence": {
                            "doc_id": "greenpeak_fy25.pdf", "page": 4,
                            "table": "Profit and Loss", "row": "Other income", "period": "FY2025"
                        }},
                        "FY2024": {"value": 42.0, "evidence": {
                            "doc_id": "greenpeak_fy25.pdf", "page": 4,
                            "table": "Profit and Loss", "row": "Other income", "period": "FY2024"
                        }},
                    }
                }
            },
            "notes": {
                "note_7_advances": {
                    "FY2025": {"value": 8500.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 8, "table": "Note 7", "row": "Advances", "period": "FY2025"}},
                    "narrative": {
                        "text": "The bank classifies all trade recievables and loan advances in accordance with RBI prudential guidelines.",
                        "evidence": {
                            "doc_id": "greenpeak_fy25.pdf", "page": 8,
                            "table": "Note 7", "row": "Narrative", "period": "FY2025"
                        }
                    }
                },
                "note_15_other_income": {
                    "FY2025": {"value": 185.0, "evidence": {
                        "doc_id": "greenpeak_fy25.pdf", "page": 10,
                        "table": "Note 15", "row": "Other income", "period": "FY2025"
                    }},
                    "narrative": {
                        "text": "Other income includes a gain of 143 crore arising from the one-off sale of investment property during FY2025.",
                        "evidence": {
                            "doc_id": "greenpeak_fy25.pdf", "page": 10,
                            "table": "Note 15", "row": "Narrative", "period": "FY2025"
                        }
                    }
                }
            }
        }
    }

    sample_findings = [
        {
            "finding_id"      : "F-MATH-001",
            "module"          : "math_engine",
            "check"           : "balance_sheet_equation",
            "status"          : "exception",
            "severity"        : "high",
            "statement"       : "balance_sheet",
            "line_item"       : "total_assets",
            "expected"        : 12410.0,
            "actual"          : 12450.0,
            "difference"      : 40.0,
            "evidence": [
                {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Total Assets", "period": "FY2025"},
                {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Total Liabilities", "period": "FY2025"},
                {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Total Equity", "period": "FY2025"}
            ],
            "ai_explanation": None
        },
        {
            "finding_id"      : "F-PY-001",
            "module"          : "consistency_engine",
            "check"           : "prior_year_movement",
            "status"          : "exception",
            "severity"        : "high",
            "statement"       : "profit_and_loss",
            "line_item"       : "other_income",
            "expected"        : "Movement within 20% threshold",
            "actual"          : "340.5% increase YoY",
            "difference"      : 143.0,
            "prior_year_value": 42.0,
            "pct_change"      : 340.5,
            "evidence": [
                {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Other income", "period": "FY2025"},
                {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Other income", "period": "FY2024"},
            ],
            "ai_explanation": None,
        }
    ]

    print("\nRunning full AI Layer test...")
    result = run(sample_canonical, sample_findings)
    print("\n=== AI LAYER OUTPUT ===")
    print(json.dumps(result, indent=2))

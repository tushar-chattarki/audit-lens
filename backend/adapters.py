"""
adapters.py — Member 7 Integration Adapters
=============================================
Normalizes findings from all three teammate engines into the
Dashboard Canonical FindingSchema shape.

Adapters:
  1. math_finding_adapter    — MathEngine Finding.to_dict() → CanonicalFinding
  2. member5_finding_adapter — Member 5 create_finding() → CanonicalFinding
  3. ai_output_adapter       — AI Layer finding dict → CanonicalFinding
  4. merge_all_findings      — Combines all adapted findings into one list
"""

from typing import Dict, Any, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER — Confidence string → float
# ═══════════════════════════════════════════════════════════════════════════════

def _confidence_to_float(c) -> float:
    """Converts AI layer confidence strings to numeric values."""
    if isinstance(c, (int, float)):
        return float(c)
    return {"high": 0.9, "medium": 0.6, "low": 0.3}.get(str(c).lower(), 0.5)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER — Normalize evidence dicts to EvidenceSchema shape
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_evidence(evidence_list: list, fallback_doc_id: str = "uploaded.pdf") -> list:
    """
    Ensures each evidence dict has the required EvidenceSchema fields:
      doc_id, page, table, row, period
    Fills defaults for any missing fields.
    """
    normalized = []
    for ev in (evidence_list or []):
        if not isinstance(ev, dict):
            continue
        normalized.append({
            "doc_id": ev.get("doc_id") or fallback_doc_id,
            "page": ev.get("page", 0) if isinstance(ev.get("page"), int) else 0,
            "table": ev.get("table") or ev.get("source", ""),
            "row": ev.get("row") or ev.get("field", ""),
            "period": ev.get("period", "")
        })
    return normalized


# ═══════════════════════════════════════════════════════════════════════════════
# ADAPTER 1 — Math Engine (feature/math-engine branch)
# ═══════════════════════════════════════════════════════════════════════════════

def math_finding_adapter(f: Dict[str, Any], doc_id: str = "uploaded.pdf") -> Dict[str, Any]:
    """
    Adapts a MathEngine Finding.to_dict() into the Dashboard CanonicalFinding shape.

    MathEngine Finding fields:
        finding_id, module, check, status, severity, expected, actual,
        difference, evidence, ai_explanation, created_at

    Key transformations:
        - Infer 'statement' from check name (missing in MathEngine)
        - Evidence list normalized to EvidenceSchema
        - Add reviewer_status / reviewer_comment defaults
    """
    check = f.get("check", "")

    # Infer statement from check name
    if "balance_sheet" in check:
        statement = "Balance Sheet"
    elif "pnl" in check or "profit" in check or "income_minus" in check:
        statement = "Profit & Loss"
    elif "cash_flow" in check:
        statement = "Cash Flow"
    elif "equity" in check:
        statement = "Statement of Changes in Equity"
    elif "subtotal" in check or "footing" in check:
        statement = "Subtotal / Footing"
    else:
        statement = "General"

    return {
        "finding_id": f.get("finding_id", ""),
        "module": "math_engine",
        "check": check,
        "statement": statement,
        "status": str(f.get("status", "not_applicable")).lower(),
        "severity": str(f.get("severity", "low")).lower(),
        "expected": f.get("expected"),
        "actual": f.get("actual"),
        "difference": f.get("difference"),
        "evidence": _normalize_evidence(f.get("evidence", []), doc_id),
        "ai_explanation": None,
        "reviewer_status": "Open",
        "reviewer_comment": ""
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ADAPTER 2 — Member 5 Consistency & Prior-Year (member5-consistency-prior-year)
# ═══════════════════════════════════════════════════════════════════════════════

# Status mapping: Member 5 UPPERCASE → Dashboard lowercase
_M5_STATUS_MAP = {
    "PASS": "pass",
    "FAIL": "exception",
    "UNUSUAL": "warning",
    "REVIEW": "not_applicable",
}

# Severity mapping: Member 5 title-case → Dashboard lowercase
_M5_SEVERITY_MAP = {
    "High": "high",
    "Medium": "medium",
    "Low": "low",
    "None": "low",
}

# Rule-to-statement mapping for Member 5
_M5_RULE_STATEMENT = {
    "C001": "Cross-Statement Consistency — Cash",
    "C002": "Cross-Statement Consistency — Cash Flow vs Notes",
    "C003": "Cross-Statement Consistency — BS vs Notes",
    "C004": "Cross-Statement Consistency — Equity Roll-Forward",
    "C005": "Cross-Statement Consistency — Depreciation vs Notes",
    "C006": "Cross-Statement Consistency — Tax vs Notes",
    "C007": "Cross-Statement Consistency — Dividends vs Notes",
    "PY001": "Prior-Year Comparison — Cash",
    "PY002": "Prior-Year Comparison — Total Assets",
    "PY003": "Prior-Year Comparison — Total Liabilities",
    "PY004": "Prior-Year Comparison — Total Equity",
    "PY005": "Prior-Year Comparison — Net Income",
    "PY006": "Prior-Year Comparison — Depreciation",
    "PY007": "Prior-Year Comparison — Tax Expense",
    "PY008": "Prior-Year Comparison — Dividends",
}


def member5_finding_adapter(f: Dict[str, Any], doc_id: str = "uploaded.pdf") -> Dict[str, Any]:
    """
    Adapts a Member 5 create_finding() dict into the Dashboard CanonicalFinding shape.

    Member 5 Finding fields:
        rule_id, category, status, severity, message, values, evidence

    Key transformations:
        - rule_id → finding_id with "F-M5-" prefix
        - category → module (consistency_engine or prior_year_engine)
        - status UPPERCASE → lowercase mapping (FAIL→exception, UNUSUAL→warning)
        - severity Title-case → lowercase mapping (None→low)
        - values dict → expected/actual extraction
        - Infer 'statement' from rule_id and category
    """
    rule_id = f.get("rule_id", "UNKNOWN")
    category = f.get("category", "")
    message = f.get("message", "")
    values = f.get("values", {})

    # Determine module from category
    if category == "consistency":
        module = "consistency_engine"
    elif category == "prior_year":
        module = "prior_year_engine"
    else:
        module = "consistency_engine"

    # Statement from rule mapping
    statement = _M5_RULE_STATEMENT.get(rule_id, f"{category.title()} Check")

    # Extract expected/actual from values dict
    # For consistency rules: values may contain {balance_sheet, cash_flow, notes}
    # For prior-year rules: values may contain {account, current_year, prior_year}
    expected = None
    actual = None
    difference = None

    if category == "prior_year":
        current_val = values.get("current_year")
        prior_val = values.get("prior_year")
        expected = prior_val
        actual = current_val
        if current_val is not None and prior_val is not None:
            try:
                difference = float(current_val) - float(prior_val)
            except (ValueError, TypeError):
                pass
    elif category == "consistency":
        # For consistency, the first value is "expected" and any differing value is "actual"
        val_keys = [k for k in values.keys() if k != "account"]
        if len(val_keys) >= 2:
            expected = values.get(val_keys[0])
            actual = values.get(val_keys[1])
            if expected is not None and actual is not None:
                try:
                    difference = float(actual) - float(expected)
                except (ValueError, TypeError):
                    pass
        elif len(val_keys) == 1:
            expected = values.get(val_keys[0])

    return {
        "finding_id": f"F-M5-{rule_id}",
        "module": module,
        "check": f"{rule_id} — {message[:80]}",
        "statement": statement,
        "status": _M5_STATUS_MAP.get(f.get("status", ""), "not_applicable"),
        "severity": _M5_SEVERITY_MAP.get(f.get("severity", ""), "low"),
        "expected": expected,
        "actual": actual,
        "difference": difference,
        "evidence": _normalize_evidence(f.get("evidence", []), doc_id),
        "ai_explanation": None,
        "reviewer_status": "Open",
        "reviewer_comment": ""
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ADAPTER 3 — AI Layer (om branch)
# ═══════════════════════════════════════════════════════════════════════════════

def ai_output_adapter(f: Dict[str, Any], doc_id: str = "uploaded.pdf") -> Dict[str, Any]:
    """
    Adapts an AI Layer finding dict into the Dashboard CanonicalFinding shape.

    AI Layer Finding fields:
        finding_id, module, check, status, severity, expected, actual,
        difference, evidence, ai_explanation (dict with text/confidence/caveats/label)

    Key transformations:
        - ai_explanation.confidence string → float
        - severity None → "low"
        - Strip internal fields (_error, _ai_error)
        - statement defaults to "AI Review" if not present
    """
    ai_expl_raw = f.get("ai_explanation")
    normalized_ai = None

    if ai_expl_raw and isinstance(ai_expl_raw, dict):
        normalized_ai = {
            "label": ai_expl_raw.get("label", "SUGGESTED — pending reviewer sign-off"),
            "text": ai_expl_raw.get("text"),
            "original_text": ai_expl_raw.get("original_text"),
            "flagged_issue": ai_expl_raw.get("flagged_issue"),
            "suggested_revision": ai_expl_raw.get("suggested_revision"),
            "confidence": _confidence_to_float(ai_expl_raw.get("confidence", "medium")),
            "caveats": ai_expl_raw.get("caveats", "Reviewer must verify before sign-off."),
            "wp514_target_field": ai_expl_raw.get("wp514_target_field"),
            "source_finding_id": ai_expl_raw.get("source_finding_id"),
        }

    # Determine statement
    check = f.get("check", "")
    if "grammar" in check:
        statement = "Narrative Disclosure"
    elif "summary" in check:
        statement = "Overall Review"
    elif f.get("statement"):
        statement = f["statement"]
    else:
        statement = "AI Review"

    return {
        "finding_id": f.get("finding_id", ""),
        "module": "ai_layer",
        "check": check,
        "statement": statement,
        "status": str(f.get("status", "pass")).lower(),
        "severity": str(f.get("severity") or "low").lower(),
        "expected": f.get("expected"),
        "actual": f.get("actual"),
        "difference": f.get("difference"),
        "evidence": _normalize_evidence(f.get("evidence", []), doc_id),
        "ai_explanation": normalized_ai,
        "reviewer_status": "Open",
        "reviewer_comment": ""
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MERGE — Combine all adapted findings into one sorted list
# ═══════════════════════════════════════════════════════════════════════════════

def merge_all_findings(
    math_findings: List[Dict[str, Any]],
    m5_findings: List[Dict[str, Any]],
    ai_findings: List[Dict[str, Any]],
    doc_id: str = "uploaded.pdf"
) -> List[Dict[str, Any]]:
    """
    Adapts and merges findings from all three engines into one canonical list.

    Order: Math Engine → Member 5 Consistency → Member 5 Prior-Year → AI Layer
    This matches the pipeline execution order and the WP-514 section flow.
    """
    merged: List[Dict[str, Any]] = []

    # 1. Math Engine findings
    for f in (math_findings or []):
        merged.append(math_finding_adapter(f, doc_id))

    # 2. Member 5 findings (consistency first, then prior-year)
    consistency = [f for f in (m5_findings or []) if f.get("category") == "consistency"]
    prior_year = [f for f in (m5_findings or []) if f.get("category") == "prior_year"]
    other_m5 = [f for f in (m5_findings or []) if f.get("category") not in ("consistency", "prior_year")]

    for f in consistency:
        merged.append(member5_finding_adapter(f, doc_id))
    for f in prior_year:
        merged.append(member5_finding_adapter(f, doc_id))
    for f in other_m5:
        merged.append(member5_finding_adapter(f, doc_id))

    # 3. AI Layer findings
    for f in (ai_findings or []):
        merged.append(ai_output_adapter(f, doc_id))

    return merged


# ═══════════════════════════════════════════════════════════════════════════════
# ENRICHMENT — Attach AI explanations to exception findings from other engines
# ═══════════════════════════════════════════════════════════════════════════════

def attach_ai_explanations(
    findings: List[Dict[str, Any]],
    ai_enriched: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    After the AI Layer enriches exception findings with ai_explanation,
    this function maps those explanations back to the canonical findings list.

    The AI Layer returns enriched copies of findings with ai_explanation populated.
    We match by finding_id and inject the ai_explanation into the original canonical finding.
    """
    # Build lookup by finding_id from AI-enriched output
    ai_lookup: Dict[str, Dict] = {}
    for af in (ai_enriched or []):
        fid = af.get("finding_id")
        ai_expl = af.get("ai_explanation")
        if fid and ai_expl and isinstance(ai_expl, dict):
            ai_lookup[fid] = ai_expl

    # Inject AI explanations into canonical findings
    for f in findings:
        fid = f.get("finding_id")
        raw = ai_lookup.get(fid) or f.get("ai_explanation")
        if raw and isinstance(raw, dict):
            f["ai_explanation"] = {
                "label": raw.get("label", "SUGGESTED — pending reviewer sign-off"),
                "text": raw.get("text"),
                "original_text": raw.get("original_text"),
                "flagged_issue": raw.get("flagged_issue"),
                "suggested_revision": raw.get("suggested_revision"),
                "confidence": _confidence_to_float(raw.get("confidence", "medium")),
                "caveats": raw.get("caveats", ""),
                "wp514_target_field": raw.get("wp514_target_field"),
                "source_finding_id": raw.get("source_finding_id"),
            }

    return findings


# ═══════════════════════════════════════════════════════════════════════════════
# KPI AGGREGATION — Build SummaryKPIs from merged canonical findings
# ═══════════════════════════════════════════════════════════════════════════════

def compute_summary_kpis(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Deterministically computes KPI counts from the canonical findings list.
    Returns a dict matching SummaryKPIsSchema.
    """
    total = len(findings)
    exceptions = sum(1 for f in findings if f.get("status") in ("exception", "fail", "warning"))
    passes = sum(1 for f in findings if f.get("status") == "pass")
    not_applicable = sum(1 for f in findings if f.get("status") == "not_applicable")

    high = sum(1 for f in findings if f.get("severity") == "high" and f.get("status") in ("exception", "fail", "warning"))
    medium = sum(1 for f in findings if f.get("severity") == "medium" and f.get("status") in ("exception", "fail", "warning"))
    low = sum(1 for f in findings if f.get("severity") == "low" and f.get("status") in ("exception", "fail", "warning"))

    return {
        "total_findings": total,
        "exceptions": exceptions,
        "passes": passes,
        "high_severity": high,
        "medium_severity": medium,
        "low_severity": low,
        "not_applicable": not_applicable,
    }


def compute_statement_summaries(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Groups findings by statement and computes per-statement pass/fail/warning counts.
    Returns a list matching List[StatementSummarySchema].
    """
    by_statement: Dict[str, List[Dict]] = {}
    for f in findings:
        stmt = f.get("statement", "General")
        by_statement.setdefault(stmt, []).append(f)

    summaries = []
    for stmt, stmt_findings in by_statement.items():
        passed = sum(1 for f in stmt_findings if f.get("status") == "pass")
        failed = sum(1 for f in stmt_findings if f.get("status") in ("exception", "fail"))
        warnings = sum(1 for f in stmt_findings if f.get("status") == "warning")
        total = len(stmt_findings)

        if failed > 0:
            overall = "EXCEPTION"
        elif warnings > 0:
            overall = "WARNING"
        else:
            overall = "PASS"

        summaries.append({
            "statement": stmt,
            "checks_performed": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "overall_status": overall,
        })

    return summaries

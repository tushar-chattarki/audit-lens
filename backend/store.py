import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from m3_converter import convert_m3_extraction_to_review, create_sunrise_bank_review

# In-memory storage dictionary for review jobs
REVIEWS_DB: Dict[str, Dict[str, Any]] = {}


def generate_dynamic_ai_summary(job_data: Dict[str, Any]) -> str:
    """
    Dynamically generates the Executive AI Review Summary text based on
    the actual review_metadata, summary_kpis, and findings from the job.
    This ensures every uploaded dataset gets an accurate, data-driven summary
    instead of the static GreenPeak fallback text.
    """
    meta = job_data.get("review_metadata", {})
    kpis = job_data.get("summary_kpis", {})
    findings: List[Dict[str, Any]] = job_data.get("findings", [])

    bank_name = meta.get("bank_name", "Unknown Entity")
    reporting_period = meta.get("reporting_period", "N/A")
    currency = meta.get("currency", "INR")
    unit = meta.get("unit", "Crores (Cr)")
    unit_short = unit.split('(')[-1].rstrip(')') if '(' in unit else unit

    total_findings = kpis.get("total_findings", len(findings))
    exceptions = kpis.get("exceptions", 0)
    passes = kpis.get("passes", 0)
    high_sev = kpis.get("high_severity", 0)
    medium_sev = kpis.get("medium_severity", 0)
    low_sev = kpis.get("low_severity", 0)

    # Build key-issues list from actual findings
    key_issues: List[str] = []
    for f in findings:
        if f.get("status") in ("fail", "exception", "warning"):
            check = f.get("check", "")
            diff = f.get("difference", 0)
            stmt = f.get("statement", "")
            ai_text = ""
            if isinstance(f.get("ai_explanation"), dict):
                ai_text = f["ai_explanation"].get("text", "")

            if diff and diff != 0:
                key_issues.append(
                    f"a {currency} {abs(diff):,.0f} {unit_short} "
                    f"{stmt} discrepancy in check '{check}'"
                )
            elif ai_text:
                # Use first sentence of AI explanation as summary
                first_sentence = ai_text.split(".")[0].strip()
                if len(first_sentence) > 120:
                    first_sentence = first_sentence[:117] + "..."
                key_issues.append(first_sentence)
            else:
                key_issues.append(f"{stmt} exception in check '{check}'")

    # Construct summary text
    summary_parts = [
        f"Automated review of {bank_name} {reporting_period} financial statements "
        f"identified {exceptions} exception{'s' if exceptions != 1 else ''} out of "
        f"{total_findings} checks performed."
    ]

    if passes > 0:
        summary_parts.append(
            f" {passes} check{'s' if passes != 1 else ''} tied out successfully."
        )

    if key_issues:
        issues_text = "; ".join(key_issues[:4])  # Limit to top 4 issues
        summary_parts.append(f" Key issues include: {issues_text}.")

    if high_sev > 0 or medium_sev > 0 or low_sev > 0:
        summary_parts.append(
            f" Severity breakdown: {high_sev} high, {medium_sev} medium, {low_sev} low."
        )

    summary_parts.append(
        " All AI narrative explanations are suggestions pending final human reviewer sign-off on WP-514."
    )

    return "".join(summary_parts)


def sync_job_ai_summary(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures that the overall_ai_summary.text and all WP-514 engagement details
    in the job data are dynamically generated from the actual bank name, KPIs,
    and findings — replacing any static/stale GreenPeak text.
    """
    meta = job_data.get("review_metadata", {})
    bank_name = meta.get("bank_name", "GreenPeak Bank Ltd.")
    bank_id = meta.get("bank_id") or bank_name.upper().replace(" ", "")[:10]
    reporting_period = meta.get("reporting_period", "FY2025")
    comparative_period = meta.get("comparative_period", "FY2024")
    currency = meta.get("currency", "INR")
    unit = meta.get("unit", "Crores (Cr)")
    source_curr = meta.get("source_document_current", f"{bank_name}_annual_report.pdf")
    source_prior = meta.get("source_document_prior", source_curr)
    review_date = meta.get("review_date", "2026-08-16")
    prepared_by = meta.get("prepared_by", "Audit Lens Engine")
    overall_status = meta.get("overall_status", "EXCEPTIONS FOUND")

    # Always regenerate the AI summary text from actual data
    dynamic_text = generate_dynamic_ai_summary(job_data)

    if "overall_ai_summary" not in job_data:
        job_data["overall_ai_summary"] = {}

    job_data["overall_ai_summary"]["text"] = dynamic_text
    job_data["overall_ai_summary"]["label"] = "Executive AI Review Summary"
    if "caveats" not in job_data["overall_ai_summary"]:
        job_data["overall_ai_summary"]["caveats"] = (
            "Generated strictly from deterministic rule findings; human reviewer sign-off mandatory."
        )

    # Sync WP-514 engagement details
    if "wp514" in job_data:
        if "engagement_details" not in job_data["wp514"]:
            job_data["wp514"]["engagement_details"] = {}
        eng = job_data["wp514"]["engagement_details"]
        eng["job_id"] = meta.get("job_id", "REV-2025-001")
        eng["bank_name"] = bank_name
        eng["bank_id"] = bank_id
        eng["reporting_period"] = reporting_period
        eng["comparative_period"] = comparative_period
        eng["currency"] = currency
        eng["unit"] = unit
        eng["source_document_current"] = source_curr
        eng["source_document_prior"] = source_prior
        eng["review_date"] = review_date
        eng["prepared_by"] = prepared_by
        eng["overall_status"] = overall_status

        if "overall_conclusion" in job_data["wp514"]:
            oc = job_data["wp514"]["overall_conclusion"]
            oc["ai_generated_review_summary"] = dynamic_text
            kpis = job_data.get("summary_kpis", {})
            total_exc = kpis.get("exceptions", 0)
            if total_exc == 0:
                oc["final_reviewer_decision"] = "APPROVED FOR AUDIT SIGN-OFF"
                oc["reviewer_comments"] = f"Deterministic checks for {bank_name} ({reporting_period}) verified clean with 0 exceptions."
            else:
                oc["final_reviewer_decision"] = "REQUIRES REVISION BY FINANCE TEAM"
                oc["reviewer_comments"] = f"Audit review for {bank_name} ({reporting_period}) identified {total_exc} exceptions requiring auditor review prior to sign-off."

    return job_data


def load_seed_fixture() -> Dict[str, Any]:
    possible_paths = [
        Path(__file__).resolve().parent.parent / "docs" / "reference" / "ai_review_sample.json",
        Path(__file__).resolve().parent.parent.parent / "docs" / "reference" / "ai_review_sample.json",
        Path(__file__).resolve().parent / "docs" / "reference" / "ai_review_sample.json",
    ]
    fixture_path = None
    for p in possible_paths:
        if p.exists():
            fixture_path = p
            break
            
    if fixture_path:
        with open(fixture_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Default fallback object if file path differs
    return {
        "review_metadata": {
            "job_id": "REV-2025-001",
            "bank_name": "GreenPeak Bank Ltd.",
            "bank_id": "GREENPEAK",
            "reporting_period": "FY2025",
            "comparative_period": "FY2024",
            "currency": "INR",
            "unit": "Crores (Cr)",
            "source_document_current": "GreenPeak_FY2025.pdf",
            "source_document_prior": "GreenPeak_FY2024.pdf",
            "review_date": "2026-08-16",
            "prepared_by": "Audit Lens Engine",
            "reviewed_by": "Pending Auditor Sign-off",
            "overall_status": "EXCEPTIONS FOUND"
        },
        "summary_kpis": {
            "total_findings": 5,
            "exceptions": 4,
            "passes": 1,
            "high_severity": 2,
            "medium_severity": 1,
            "low_severity": 1,
            "not_applicable": 0
        },
        "statement_summaries": [
            {
                "statement": "Balance Sheet",
                "checks_performed": 2,
                "passed": 0,
                "failed": 2,
                "warnings": 0,
                "overall_status": "EXCEPTION"
            }
        ],
        "canonical_metrics": {
            "net_income": {"current": 21600, "prior": 13500, "change_pct": 60.0}
        },
        "findings": [],
        "overall_ai_summary": {
            "text": "Automated review identified 4 exceptions.",
            "caveats": "Human reviewer sign-off mandatory.",
            "label": "Executive AI Review Summary"
        }
    }


def get_job(job_id: str) -> Dict[str, Any]:
    job_id_lower = job_id.lower()

    # Sunrise National Bank dataset
    if "sunrise" in job_id_lower or "sun" in job_id_lower:
        if job_id not in REVIEWS_DB:
            REVIEWS_DB[job_id] = create_sunrise_bank_review()
        return sync_job_ai_summary(REVIEWS_DB[job_id])

    # Horizon NBFC dataset (Member 3 extraction)
    if "horizon" in job_id_lower or "job-001" in job_id_lower or "job-horizon" in job_id_lower:
        if job_id not in REVIEWS_DB:
            hz_file = Path(__file__).parent / "m3_data_extraction.json"
            if hz_file.exists():
                with open(hz_file, "r", encoding="utf-8") as f:
                    hz_json = json.load(f)
                REVIEWS_DB[job_id] = convert_m3_extraction_to_review(hz_json)
            else:
                REVIEWS_DB[job_id] = load_seed_fixture()
        return sync_job_ai_summary(REVIEWS_DB[job_id])

    # Default / GreenPeak / any other upload
    if job_id not in REVIEWS_DB or "wp514" not in REVIEWS_DB[job_id]:
        seed = load_seed_fixture()
        seed["review_metadata"]["job_id"] = job_id
        REVIEWS_DB[job_id] = seed

    return sync_job_ai_summary(REVIEWS_DB[job_id])


def save_job(job_id: str, data: Dict[str, Any]) -> None:
    sync_job_ai_summary(data)
    REVIEWS_DB[job_id] = data


def update_finding(job_id: str, finding_id: str, reviewer_status: str, reviewer_comment: str) -> Optional[Dict[str, Any]]:
    job = get_job(job_id)
    findings = job.get("findings", [])
    for f in findings:
        if f.get("finding_id") == finding_id:
            f["reviewer_status"] = reviewer_status
            f["reviewer_comment"] = reviewer_comment
            return f

    # Fallback: search across all active jobs in REVIEWS_DB
    for j_id, j_data in REVIEWS_DB.items():
        for f in j_data.get("findings", []):
            if f.get("finding_id") == finding_id:
                f["reviewer_status"] = reviewer_status
                f["reviewer_comment"] = reviewer_comment
                return f

    return None

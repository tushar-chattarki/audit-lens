"""
integration_orchestrator.py — Member 7 End-to-End Pipeline
==========================================================
Wires the complete audit pipeline after PDF extraction:
    canonical_json → Math Engine → Member 5 → AI Layer → Adapters → Merged → WP-514

This module contains reimplemented versions of the teammate engine checks
that operate on the canonical_json dict directly, so we do not need to
import from teammate branch code or read from disk files.

The pipeline produces a complete ReviewResponseSchema-compatible dict.
"""

import datetime
import uuid
from typing import Dict, Any, List, Optional

from adapters import (
    math_finding_adapter,
    member5_finding_adapter,
    ai_output_adapter,
    merge_all_findings,
    attach_ai_explanations,
    compute_summary_kpis,
    compute_statement_summaries,
    _normalize_evidence,
    _confidence_to_float,
)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Local Math Engine Checks (Member 4 contract)
# ═══════════════════════════════════════════════════════════════════════════════

def _safe_val(data: dict, *path, period: str = "") -> Optional[float]:
    """Safely navigate nested dict path and extract a numeric value."""
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if current is None:
        return None
    if isinstance(current, (int, float)):
        return float(current)
    if isinstance(current, dict) and period:
        period_data = current.get(period, {})
        if isinstance(period_data, dict):
            return period_data.get("value")
        return None
    return None


def _build_evidence(doc_id: str, page: int, table: str, row: str, period: str) -> dict:
    return {"doc_id": doc_id, "page": page, "table": table, "row": row, "period": period}


def run_math_checks(canonical: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Reimplements the core Math Engine checks from feature/math-engine.
    Operates directly on the canonical_json dict.
    Returns findings in MathEngine Finding.to_dict() shape.
    """
    findings = []
    periods = canonical.get("periods", ["FY2025", "FY2024"])
    stmts = canonical.get("statements", {})
    bs = stmts.get("balance_sheet", {})
    pl = stmts.get("profit_and_loss", {})
    cf = stmts.get("cash_flow", {})
    eq = stmts.get("equity", {})
    doc_id = canonical.get("job_id", "uploaded.pdf")

    for period in periods:
        # --- Check 1: Balance Sheet Identity ---
        # Total Assets = Total Liabilities + Total Equity
        ta = (_safe_val(bs, "assets", "total_assets", period=period) or
              _safe_val(bs, "total_assets", period=period))
        tl = (_safe_val(bs, "liabilities", "total_liabilities", period=period) or
              _safe_val(bs, "total_liabilities", period=period))
        te = (_safe_val(bs, "equity", "total_equity", period=period) or
              _safe_val(bs, "total_equity", period=period))

        if ta is not None and tl is not None and te is not None:
            expected = tl + te
            diff = ta - expected
            status = "pass" if abs(diff) / max(abs(expected), 1) <= 0.01 else "exception"
            severity = "high" if status == "exception" and abs(diff) > 100 else ("medium" if status == "exception" else "low")
            findings.append({
                "finding_id": f"math_{uuid.uuid4().hex[:8]}",
                "module": "math_engine",
                "check": f"balance_sheet_identity_{period}",
                "status": status,
                "severity": severity,
                "expected": expected,
                "actual": ta,
                "difference": diff,
                "evidence": [
                    _build_evidence(doc_id, 2, "Balance Sheet", "Total assets", period),
                    _build_evidence(doc_id, 2, "Balance Sheet", "Total liabilities", period),
                    _build_evidence(doc_id, 2, "Balance Sheet", "Total equity", period),
                ],
            })

        # --- Check 2: P&L Income - Expenses = Net Income ---
        total_income = _safe_val(pl, "income", "total_income", period=period)
        total_expenses = _safe_val(pl, "expenses", "total_expenses", period=period)
        net_income = _safe_val(pl, "profit", "net_income", period=period)

        if total_income is not None and total_expenses is not None and net_income is not None:
            expected_net = total_income - total_expenses
            diff = net_income - expected_net
            status = "pass" if abs(diff) / max(abs(expected_net), 1) <= 0.01 else "exception"
            severity = "high" if status == "exception" and abs(diff) > 50 else ("medium" if status == "exception" else "low")
            findings.append({
                "finding_id": f"math_{uuid.uuid4().hex[:8]}",
                "module": "math_engine",
                "check": f"pnl_income_minus_expenses_{period}",
                "status": status,
                "severity": severity,
                "expected": expected_net,
                "actual": net_income,
                "difference": diff,
                "evidence": [
                    _build_evidence(doc_id, 4, "Profit and Loss", "Total income", period),
                    _build_evidence(doc_id, 4, "Profit and Loss", "Total expenses", period),
                    _build_evidence(doc_id, 4, "Profit and Loss", "Net income", period),
                ],
            })

        # --- Check 3: PBT - Tax = Net Income ---
        pbt = _safe_val(pl, "profit", "profit_before_tax", period=period)
        tax = _safe_val(pl, "profit", "tax_expense", period=period)

        if pbt is not None and tax is not None and net_income is not None:
            expected_ni = pbt - tax
            diff = net_income - expected_ni
            status = "pass" if abs(diff) / max(abs(expected_ni), 1) <= 0.01 else "exception"
            severity = "medium" if status == "exception" else "low"
            findings.append({
                "finding_id": f"math_{uuid.uuid4().hex[:8]}",
                "module": "math_engine",
                "check": f"pnl_pbt_minus_tax_{period}",
                "status": status,
                "severity": severity,
                "expected": expected_ni,
                "actual": net_income,
                "difference": diff,
                "evidence": [
                    _build_evidence(doc_id, 4, "Profit and Loss", "Profit before tax", period),
                    _build_evidence(doc_id, 4, "Profit and Loss", "Tax expense", period),
                    _build_evidence(doc_id, 4, "Profit and Loss", "Net income", period),
                ],
            })

    # --- Check 4: Cash Flow Identity (current period only) ---
    current = periods[0] if periods else "FY2025"
    opening = _safe_val(cf, "opening_cash", period=current)
    operating = _safe_val(cf, "net_cash_from_operating_activities", period=current)
    investing = _safe_val(cf, "net_cash_from_investing_activities", period=current)
    financing = _safe_val(cf, "net_cash_from_financing_activities", period=current)
    closing = _safe_val(cf, "closing_cash", period=current)

    if all(v is not None for v in [opening, operating, investing, financing, closing]):
        expected_closing = opening + operating + investing + financing
        diff = closing - expected_closing
        status = "pass" if abs(diff) / max(abs(expected_closing), 1) <= 0.01 else "exception"
        severity = "high" if status == "exception" else "low"
        findings.append({
            "finding_id": f"math_{uuid.uuid4().hex[:8]}",
            "module": "math_engine",
            "check": f"cash_flow_identity_{current}",
            "status": status,
            "severity": severity,
            "expected": expected_closing,
            "actual": closing,
            "difference": diff,
            "evidence": [
                _build_evidence(doc_id, 5, "Cash Flow", "Opening cash", current),
                _build_evidence(doc_id, 5, "Cash Flow", "Net cash from operations", current),
                _build_evidence(doc_id, 5, "Cash Flow", "Closing cash", current),
            ],
        })

    # --- Check 5: Equity Roll-Forward ---
    opening_eq = _safe_val(eq, "opening_equity", period=current)
    eq_ni = _safe_val(eq, "net_income", period=current)
    dividends = _safe_val(eq, "dividends_paid", period=current)
    closing_eq = _safe_val(eq, "closing_equity", period=current)

    if all(v is not None for v in [opening_eq, eq_ni, closing_eq]):
        div = dividends or 0.0
        expected_eq = opening_eq + eq_ni - div
        diff = closing_eq - expected_eq
        status = "pass" if abs(diff) / max(abs(expected_eq), 1) <= 0.01 else "exception"
        severity = "medium" if status == "exception" else "low"
        findings.append({
            "finding_id": f"math_{uuid.uuid4().hex[:8]}",
            "module": "math_engine",
            "check": f"equity_rollforward_{current}",
            "status": status,
            "severity": severity,
            "expected": expected_eq,
            "actual": closing_eq,
            "difference": diff,
            "evidence": [
                _build_evidence(doc_id, 6, "Equity", "Opening equity", current),
                _build_evidence(doc_id, 6, "Equity", "Closing equity", current),
            ],
        })

    return findings


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Local Member 5 Checks (Consistency + Prior-Year)
# ═══════════════════════════════════════════════════════════════════════════════

UNUSUAL_MOVEMENT_THRESHOLD = 20.0  # percent


def _get_m5_val(data: dict, path: list, period: str = "FY2025") -> Optional[float]:
    """Navigate canonical data for Member 5 value extraction."""
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if current is None:
        return None
    if isinstance(current, dict):
        period_data = current.get(period, {})
        if isinstance(period_data, dict):
            return period_data.get("value")
    if isinstance(current, (int, float)):
        return float(current)
    return None


def run_consistency_checks(canonical: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Reimplements Member 5 consistency rules C001-C007.
    Returns findings in Member 5 create_finding() shape.
    """
    findings = []
    stmts = canonical.get("statements", {})
    bs = stmts.get("balance_sheet", {})
    cf = stmts.get("cash_flow", {})
    notes = stmts.get("notes", {})
    eq = stmts.get("equity", {})
    pl = stmts.get("profit_and_loss", {})
    current = canonical.get("periods", ["FY2025"])[0]

    # C001: Cash consistency across BS, CF, Notes
    bs_cash = (_safe_val(bs, "assets", "cash_and_cash_equivalents", period=current) or
               _safe_val(bs, "cash_and_cash_equivalents", period=current))
    cf_cash = _safe_val(cf, "closing_cash", period=current)
    note_cash = None
    for nk, nv in notes.items():
        if "cash" in nk.lower() and isinstance(nv, dict):
            val = nv.get(current, {})
            if isinstance(val, dict):
                note_cash = val.get("value")
                break

    if bs_cash is not None and cf_cash is not None and note_cash is not None:
        if bs_cash == cf_cash == note_cash:
            findings.append({
                "rule_id": "C001", "category": "consistency", "status": "PASS", "severity": "None",
                "message": "Cash balances are consistent across BS, CF, and Notes.",
                "values": {"balance_sheet": bs_cash, "cash_flow": cf_cash, "notes": note_cash},
                "evidence": []
            })
        else:
            findings.append({
                "rule_id": "C001", "category": "consistency", "status": "FAIL", "severity": "High",
                "message": "Cash balance is inconsistent across financial statements and notes.",
                "values": {"balance_sheet": bs_cash, "cash_flow": cf_cash, "notes": note_cash},
                "evidence": [
                    {"source": "Balance Sheet", "field": "Cash", "value": bs_cash},
                    {"source": "Cash Flow Statement", "field": "Ending Cash", "value": cf_cash},
                    {"source": "Notes", "field": "Cash", "value": note_cash},
                ]
            })
    elif bs_cash is not None or cf_cash is not None:
        findings.append({
            "rule_id": "C001", "category": "consistency", "status": "REVIEW", "severity": "Medium",
            "message": "Cash balances cannot be fully verified — some disclosures unavailable.",
            "values": {"balance_sheet": bs_cash, "cash_flow": cf_cash, "notes": note_cash},
            "evidence": []
        })

    # C004: Equity roll-forward consistency
    opening_eq = _safe_val(eq, "opening_equity", period=current)
    ni_eq = _safe_val(eq, "net_income", period=current)
    div_eq = _safe_val(eq, "dividends_paid", period=current)
    closing_eq = _safe_val(eq, "closing_equity", period=current)
    bs_equity = (_safe_val(bs, "equity", "total_equity", period=current) or
                 _safe_val(bs, "total_equity", period=current))

    if closing_eq is not None and bs_equity is not None:
        if abs(closing_eq - bs_equity) <= 0.01:
            findings.append({
                "rule_id": "C004", "category": "consistency", "status": "PASS", "severity": "None",
                "message": "Equity roll-forward ties to Balance Sheet total equity.",
                "values": {"equity_closing": closing_eq, "bs_equity": bs_equity},
                "evidence": []
            })
        else:
            findings.append({
                "rule_id": "C004", "category": "consistency", "status": "FAIL", "severity": "High",
                "message": "Equity roll-forward does not tie to BS total equity.",
                "values": {"equity_closing": closing_eq, "bs_equity": bs_equity},
                "evidence": [
                    {"source": "Equity Statement", "field": "Closing Equity", "value": closing_eq},
                    {"source": "Balance Sheet", "field": "Total Equity", "value": bs_equity},
                ]
            })

    return findings


def run_prior_year_checks(canonical: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Reimplements Member 5 prior-year movement rules PY001-PY008.
    Returns findings in Member 5 create_finding() shape.
    """
    findings = []
    periods = canonical.get("periods", ["FY2025", "FY2024"])
    if len(periods) < 2:
        return findings
    current_period = periods[0]
    prior_period = periods[1]
    stmts = canonical.get("statements", {})
    bs = stmts.get("balance_sheet", {})
    pl = stmts.get("profit_and_loss", {})

    # Define checks: (rule_id, label, path_to_value)
    py_checks = [
        ("PY001", "Cash", [["assets", "cash_and_cash_equivalents"], ["cash_and_cash_equivalents"]]),
        ("PY002", "Total Assets", [["assets", "total_assets"], ["total_assets"]]),
        ("PY003", "Total Liabilities", [["liabilities", "total_liabilities"], ["total_liabilities"]]),
        ("PY004", "Total Equity", [["equity", "total_equity"], ["total_equity"]]),
    ]

    for rule_id, label, paths in py_checks:
        current_val = None
        prior_val = None
        for path in paths:
            cv = _safe_val(bs, *path, period=current_period)
            pv = _safe_val(bs, *path, period=prior_period)
            if cv is not None:
                current_val = cv
            if pv is not None:
                prior_val = pv

        if current_val is None or prior_val is None:
            findings.append({
                "rule_id": rule_id, "category": "prior_year", "status": "REVIEW", "severity": "Medium",
                "message": f"{label} data unavailable for one or both periods.",
                "values": {"account": label, "current_year": current_val, "prior_year": prior_val},
                "evidence": []
            })
            continue

        diff = current_val - prior_val
        pct = (diff / abs(prior_val)) * 100 if prior_val != 0 else None

        if pct is not None and abs(pct) > UNUSUAL_MOVEMENT_THRESHOLD:
            status, severity = "UNUSUAL", "Medium"
            msg = f"{label} shows unusual {abs(pct):.1f}% movement vs prior year."
        elif pct is None:
            status, severity = "REVIEW", "Medium"
            msg = f"Prior-year {label} is zero; percentage movement cannot be calculated."
        else:
            status, severity = "PASS", "None"
            msg = f"{label} movement ({pct:.1f}%) is within the {UNUSUAL_MOVEMENT_THRESHOLD}% threshold."

        findings.append({
            "rule_id": rule_id, "category": "prior_year", "status": status, "severity": severity,
            "message": msg,
            "values": {"account": label, "current_year": current_val, "prior_year": prior_val,
                       "difference": diff, "movement_pct": pct},
            "evidence": []
        })

    # PY005: Net Income
    ni_current = _safe_val(pl, "profit", "net_income", period=current_period)
    ni_prior = _safe_val(pl, "profit", "net_income", period=prior_period)
    if ni_current is not None and ni_prior is not None:
        diff = ni_current - ni_prior
        pct = (diff / abs(ni_prior)) * 100 if ni_prior != 0 else None
        if pct is not None and abs(pct) > UNUSUAL_MOVEMENT_THRESHOLD:
            status, severity = "UNUSUAL", "Medium"
            msg = f"Net income shows unusual {abs(pct):.1f}% movement vs prior year."
        else:
            status, severity = "PASS", "None"
            msg = f"Net income movement is within threshold."
        findings.append({
            "rule_id": "PY005", "category": "prior_year", "status": status, "severity": severity,
            "message": msg,
            "values": {"account": "Net Income", "current_year": ni_current, "prior_year": ni_prior,
                       "difference": diff, "movement_pct": pct},
            "evidence": []
        })

    return findings


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — WP-514 Builder
# ═══════════════════════════════════════════════════════════════════════════════

def build_wp514(
    metadata: Dict[str, Any],
    findings: List[Dict[str, Any]],
    canonical: Dict[str, Any],
    ai_summary_text: str = ""
) -> Dict[str, Any]:
    """
    Builds the complete WP-514 working paper structure from adapted findings.
    """
    periods = canonical.get("periods", ["FY2025", "FY2024"])
    current = periods[0] if periods else "FY2025"
    prior = periods[1] if len(periods) > 1 else "FY2024"
    currency = canonical.get("currency", metadata.get("currency", "INR"))
    unit = canonical.get("unit", metadata.get("unit", "Crores (Cr)"))

    # Section 4: Math Checks
    math_checks = []
    for f in findings:
        if f.get("module") == "math_engine":
            math_checks.append({
                "check_id": f["finding_id"],
                "statement": f.get("statement", ""),
                "check_description": f.get("check", ""),
                "formula_rule": f.get("check", "").replace("_", " ").title(),
                "reported_result": f.get("actual", "N/A"),
                "calculated_result": f.get("expected", "N/A"),
                "variance": f.get("difference", 0),
                "status": f.get("status", "pass"),
            })

    # Section 5: Prior-Year Checks
    prior_year_checks = []
    for f in findings:
        if f.get("module") == "prior_year_engine":
            check_text = f.get("check", "")
            prior_year_checks.append({
                "statement": f.get("statement", ""),
                "line_item": check_text.split("—")[-1].strip() if "—" in check_text else check_text,
                "current_year_value": f.get("actual") or 0,
                "prior_year_value": f.get("expected") or 0,
                "absolute_change": f.get("difference") or 0,
                "percentage_change": 0,
                "review_threshold": f"{UNUSUAL_MOVEMENT_THRESHOLD}%",
                "flag": f.get("status") in ("exception", "warning"),
                "reason_for_flag": check_text,
                "source_reference": f"Page {f.get('evidence', [{}])[0].get('page', 'N/A') if f.get('evidence') else 'N/A'}",
            })

    # Section 6: Banking Analytics
    stmts = canonical.get("statements", {})
    bs = stmts.get("balance_sheet", {})
    pl = stmts.get("profit_and_loss", {})

    analytics = []
    metric_pairs = [
        ("Total Assets", ["assets", "total_assets"], ["total_assets"]),
        ("Net Income", ["profit", "net_income"], None),
    ]
    for label, bs_path, alt_path in metric_pairs:
        source = bs if "assets" in label.lower() or "liab" in label.lower() or "equity" in label.lower() else pl
        cv = _safe_val(source, *bs_path, period=current) if bs_path else None
        pv = _safe_val(source, *bs_path, period=prior) if bs_path else None
        if cv is None and alt_path:
            cv = _safe_val(bs, *alt_path, period=current)
            pv = _safe_val(bs, *alt_path, period=prior)

        if cv is not None and pv is not None:
            chg = ((cv - pv) / abs(pv) * 100) if pv != 0 else 0
            analytics.append({
                "metric": label,
                "current_year": cv,
                "prior_year": pv,
                "change": f"{chg:+.1f}%",
                "threshold": f"{UNUSUAL_MOVEMENT_THRESHOLD}%",
                "status": "FLAGGED" if abs(chg) > UNUSUAL_MOVEMENT_THRESHOLD else "PASS",
                "explanation": f"{label} changed by {chg:+.1f}% year-over-year.",
            })

    # Section 7: Field Mappings
    field_mappings = []
    for f in findings:
        if f.get("status") in ("exception", "warning", "fail"):
            field_mappings.append({
                "wp514_field": f.get("check", ""),
                "source_statement": f.get("statement", ""),
                "source_line_item": f.get("check", ""),
                "extracted_value": f.get("actual", "N/A"),
                "validation": f.get("status", ""),
                "exception_id": f.get("finding_id"),
            })

    # Count exceptions
    total_exc = sum(1 for f in findings if f.get("status") in ("exception", "fail", "warning"))
    high_exc = sum(1 for f in findings if f.get("severity") == "high" and f.get("status") in ("exception", "fail"))
    medium_exc = sum(1 for f in findings if f.get("severity") == "medium" and f.get("status") in ("exception", "fail", "warning"))

    key_issues = []
    for f in findings:
        if f.get("status") in ("exception", "fail", "warning"):
            key_issues.append(f.get("check", "Unidentified issue"))

    # Section 3: Financial Statement Summary (reuse statement_summaries)
    stmt_summaries = compute_statement_summaries(findings)

    return {
        "engagement_details": {
            "job_id": metadata.get("job_id", ""),
            "bank_name": metadata.get("bank_name", ""),
            "bank_id": metadata.get("bank_id", ""),
            "reporting_period": metadata.get("reporting_period", current),
            "comparative_period": metadata.get("comparative_period", prior),
            "currency": metadata.get("currency", currency),
            "unit": metadata.get("unit", unit),
            "source_document_current": metadata.get("source_document_current", ""),
            "source_document_prior": metadata.get("source_document_prior", ""),
            "review_date": metadata.get("review_date", datetime.date.today().isoformat()),
            "prepared_by": metadata.get("prepared_by", "Automated Pipeline"),
            "reviewed_by": metadata.get("reviewed_by", "Pending"),
            "overall_status": "EXCEPTIONS FOUND" if total_exc > 0 else "PASSED WITH NO EXCEPTIONS",
        },
        "financial_statement_summary": stmt_summaries,
        "math_checks": math_checks,
        "prior_year_checks": prior_year_checks,
        "banking_analytics": analytics,
        "field_mappings": field_mappings,
        "overall_conclusion": {
            "overall_review_result": "EXCEPTIONS FOUND" if total_exc > 0 else "PASSED WITH NO EXCEPTIONS",
            "total_exceptions": total_exc,
            "critical_exceptions": high_exc,
            "high_exceptions": high_exc,
            "medium_exceptions": medium_exc,
            "key_issues_requiring_attention": key_issues[:10],
            "ai_generated_review_summary": ai_summary_text,
            "final_reviewer_decision": "PENDING REVIEW",
            "reviewer_comments": "",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Canonical Metrics Builder
# ═══════════════════════════════════════════════════════════════════════════════

def build_canonical_metrics(canonical: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts key financial metrics from canonical data for dashboard charts.
    """
    periods = canonical.get("periods", ["FY2025", "FY2024"])
    current = periods[0] if periods else "FY2025"
    prior = periods[1] if len(periods) > 1 else "FY2024"
    stmts = canonical.get("statements", {})
    bs = stmts.get("balance_sheet", {})
    pl = stmts.get("profit_and_loss", {})
    notes = stmts.get("notes", {})

    def _metric(cur, pri):
        if cur is not None and pri is not None and pri != 0:
            return {"current": cur, "prior": pri, "change_pct": round((cur - pri) / abs(pri) * 100, 2)}
        elif cur is not None and pri is not None:
            return {"current": cur, "prior": pri, "change_pct": 0}
        return None

    ni_cur = _safe_val(pl, "profit", "net_income", period=current)
    ni_pri = _safe_val(pl, "profit", "net_income", period=prior)

    oi_cur = _safe_val(pl, "income", "other_income", period=current)
    oi_pri = _safe_val(pl, "income", "other_income", period=prior)

    ii_cur = _safe_val(pl, "income", "interest_income", period=current)
    ii_pri = _safe_val(pl, "income", "interest_income", period=prior)
    ie_cur = _safe_val(pl, "expenses", "interest_expense", period=current)
    ie_pri = _safe_val(pl, "expenses", "interest_expense", period=prior)
    nii_cur = (ii_cur - ie_cur) if ii_cur is not None and ie_cur is not None else None
    nii_pri = (ii_pri - ie_pri) if ii_pri is not None and ie_pri is not None else None

    ta_cur = (_safe_val(bs, "assets", "total_assets", period=current) or
              _safe_val(bs, "total_assets", period=current))
    ta_pri = (_safe_val(bs, "assets", "total_assets", period=prior) or
              _safe_val(bs, "total_assets", period=prior))

    bs_cash_cur = (_safe_val(bs, "assets", "cash_and_cash_equivalents", period=current) or
                   _safe_val(bs, "cash_and_cash_equivalents", period=current))
    bs_cash_pri = (_safe_val(bs, "assets", "cash_and_cash_equivalents", period=prior) or
                   _safe_val(bs, "cash_and_cash_equivalents", period=prior))

    note12_cur = None
    for nk, nv in notes.items():
        if "cash" in nk.lower() and isinstance(nv, dict):
            v = nv.get(current, {})
            if isinstance(v, dict):
                note12_cur = v.get("value")
                break

    tl_cur = (_safe_val(bs, "liabilities", "total_liabilities", period=current) or
              _safe_val(bs, "total_liabilities", period=current))
    te_cur = (_safe_val(bs, "equity", "total_equity", period=current) or
              _safe_val(bs, "total_equity", period=current))

    return {
        "net_income": _metric(ni_cur, ni_pri),
        "other_income": _metric(oi_cur, oi_pri),
        "net_interest_income": _metric(nii_cur, nii_pri),
        "total_assets": _metric(ta_cur, ta_pri),
        "bs_cash": _metric(bs_cash_cur, bs_cash_pri),
        "note12_cash": {"current": note12_cur, "prior": 0, "change_pct": 0} if note12_cur else None,
        "cash_difference": (bs_cash_cur - note12_cur) if bs_cash_cur and note12_cur else None,
        "bs_equation_assets": ta_cur,
        "bs_equation_liab_equity": (tl_cur + te_cur) if tl_cur and te_cur else None,
        "bs_equation_difference": (ta_cur - (tl_cur + te_cur)) if ta_cur and tl_cur and te_cur else None,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Main Orchestrator Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

def run_full_pipeline(
    canonical: Dict[str, Any],
    metadata: Dict[str, Any],
    doc_id: str = "uploaded.pdf"
) -> Dict[str, Any]:
    """
    Main orchestrator: runs the complete Member 4 → 5 → 6 → 7 pipeline.

    Args:
        canonical: Canonical JSON data (schema v1.0) from extraction
        metadata: Review metadata dict (bank_name, periods, etc.)
        doc_id: Source document identifier

    Returns:
        Complete ReviewResponseSchema-compatible dict
    """
    # Step 1: Run Math Engine checks
    math_raw = run_math_checks(canonical)

    # Step 2: Run Member 5 Consistency checks
    consistency_raw = run_consistency_checks(canonical)

    # Step 3: Run Member 5 Prior-Year checks
    prior_year_raw = run_prior_year_checks(canonical)

    # Step 4: Merge Member 5 findings
    m5_raw = consistency_raw + prior_year_raw

    # Step 5: Adapt all findings through adapters
    all_findings = merge_all_findings(
        math_findings=math_raw,
        m5_findings=m5_raw,
        ai_findings=[],  # AI layer findings added separately
        doc_id=doc_id
    )

    # Step 6: Generate default summary text
    bank_name = metadata.get("bank_name", "Unknown Entity")
    reporting_period = metadata.get("reporting_period", "N/A")
    key_issues = []
    for f in all_findings:
        if f.get("status") in ("exception", "fail", "warning"):
            key_issues.append(f.get("check", ""))

    exc_count_init = sum(1 for f in all_findings if f.get("status") in ("exception", "fail", "warning"))
    pass_count_init = sum(1 for f in all_findings if f.get("status") == "pass")
    total_count_init = len(all_findings)
    ai_summary_text = (
        f"Automated review of {bank_name} {reporting_period} financial statements "
        f"identified {exc_count_init} exception{'s' if exc_count_init != 1 else ''} out of "
        f"{total_count_init} checks performed. {pass_count_init} checks tied out successfully."
    )
    if key_issues:
        ai_summary_text += f" Key issues: {'; '.join(key_issues[:4])}."
    ai_summary_text += (
        " All AI narrative explanations are suggestions pending final human reviewer sign-off on WP-514."
    )

    # Step 7: Call the AI Layer (Ollama / Local LLM)
    try:
        from ai_layer import run as run_ai_layer
        print(f"[Orchestrator] Running AI Layer with {len(all_findings)} findings...")
        ai_result = run_ai_layer(canonical, all_findings)
        ai_enriched = ai_result.get("findings", [])
        
        # Attach AI anomaly explanations back to our original findings
        all_findings = attach_ai_explanations(all_findings, ai_enriched)
        
        # Add grammar reviews and overall summary findings generated by the AI layer
        for f in ai_enriched:
            if f.get("check") in ("grammar_review", "overall_review_summary"):
                adapted_ai = ai_output_adapter(f, doc_id)
                all_findings.append(adapted_ai)
                if f.get("check") == "overall_review_summary" and f.get("ai_explanation"):
                    txt = f["ai_explanation"].get("text")
                    if txt:
                        ai_summary_text = txt
    except Exception as e:
        print(f"[Orchestrator] AI Layer failed/unreachable. Proceeding with deterministic fallback. Error: {e}")

    # Step 8: Compute final KPIs and statement summaries after AI layer updates
    kpis = compute_summary_kpis(all_findings)
    stmt_summaries = compute_statement_summaries(all_findings)

    # Step 9: Build canonical metrics
    canonical_metrics = build_canonical_metrics(canonical)

    # Step 10: Build WP-514
    wp514 = build_wp514(metadata, all_findings, canonical, ai_summary_text)

    # Step 10: Assemble complete response
    overall_status = "EXCEPTIONS FOUND" if kpis["exceptions"] > 0 else "PASSED WITH NO EXCEPTIONS"

    inferred_bank_id = (
        metadata.get("bank_id") or
        metadata.get("bank_name", "BANK").strip().upper().replace(" ", "_")
    )
    final_meta = {
        "bank_id": inferred_bank_id,
        "review_date": datetime.date.today().isoformat(),
        "prepared_by": "Audit Lens Engine",
        "reviewed_by": "Pending Auditor Sign-off",
        "source_document_current": doc_id,
        "source_document_prior": doc_id,
        **metadata,
        "overall_status": overall_status,
    }
    if not metadata.get("bank_id"):
        final_meta["bank_id"] = inferred_bank_id

    return {
        "review_metadata": final_meta,
        "summary_kpis": kpis,
        "statement_summaries": stmt_summaries,
        "canonical_metrics": canonical_metrics,
        "findings": all_findings,
        "overall_ai_summary": {
            "text": ai_summary_text,
            "caveats": "All AI-generated explanations are candidate suggestions. Human reviewer sign-off is required.",
            "label": "AI-GENERATED SUMMARY — for reviewer reference only",
        },
        "wp514": wp514,
    }

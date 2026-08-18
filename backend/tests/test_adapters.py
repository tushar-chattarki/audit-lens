"""
test_adapters.py — Unit Tests for Member 7 Integration Adapters
================================================================
Validates that each adapter correctly normalizes teammate engine outputs
into the Dashboard CanonicalFinding shape.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from adapters import (
    math_finding_adapter,
    member5_finding_adapter,
    ai_output_adapter,
    merge_all_findings,
    compute_summary_kpis,
    compute_statement_summaries,
    _confidence_to_float,
)


def test_math_finding_adapter_pass():
    raw = {
        "finding_id": "math_abc12345",
        "module": "math_engine",
        "check": "balance_sheet_identity_FY2025",
        "status": "pass",
        "severity": "low",
        "expected": 13500.0,
        "actual": 13500.0,
        "difference": 0.0,
        "evidence": [
            {"doc_id": "test.pdf", "page": 2, "table": "Balance Sheet", "row": "Total assets", "period": "FY2025"}
        ],
        "created_at": "2026-08-19T00:00:00"
    }
    result = math_finding_adapter(raw)
    assert result["finding_id"] == "math_abc12345"
    assert result["module"] == "math_engine"
    assert result["statement"] == "Balance Sheet"
    assert result["status"] == "pass"
    assert result["severity"] == "low"
    assert result["reviewer_status"] == "Open"
    assert result["reviewer_comment"] == ""
    assert len(result["evidence"]) == 1
    assert result["evidence"][0]["doc_id"] == "test.pdf"
    print("[OK] test_math_finding_adapter_pass")


def test_math_finding_adapter_exception():
    raw = {
        "finding_id": "math_def67890",
        "module": "math_engine",
        "check": "pnl_income_minus_expenses_FY2025",
        "status": "exception",
        "severity": "high",
        "expected": 480.0,
        "actual": 360.0,
        "difference": -120.0,
        "evidence": [],
    }
    result = math_finding_adapter(raw)
    assert result["statement"] == "Profit & Loss"
    assert result["status"] == "exception"
    assert result["severity"] == "high"
    print("[OK] test_math_finding_adapter_exception")


def test_math_finding_adapter_cash_flow():
    raw = {
        "finding_id": "math_cf123",
        "module": "math_engine",
        "check": "cash_flow_identity_FY2025",
        "status": "pass",
        "severity": "low",
        "expected": 1270.0,
        "actual": 1270.0,
        "difference": 0.0,
        "evidence": [],
    }
    result = math_finding_adapter(raw)
    assert result["statement"] == "Cash Flow"
    print("[OK] test_math_finding_adapter_cash_flow")


def test_member5_finding_adapter_pass():
    raw = {
        "rule_id": "C001",
        "category": "consistency",
        "status": "PASS",
        "severity": "None",
        "message": "Cash balances are consistent across BS, CF, and Notes.",
        "values": {"balance_sheet": 1250.0, "cash_flow": 1250.0, "notes": 1250.0},
        "evidence": []
    }
    result = member5_finding_adapter(raw)
    assert result["finding_id"] == "F-M5-C001"
    assert result["module"] == "consistency_engine"
    assert result["status"] == "pass"
    assert result["severity"] == "low"  # "None" -> "low"
    assert "C001" in result["check"]
    assert "Cross-Statement Consistency" in result["statement"]
    print("[OK] test_member5_finding_adapter_pass")


def test_member5_finding_adapter_fail():
    raw = {
        "rule_id": "C001",
        "category": "consistency",
        "status": "FAIL",
        "severity": "High",
        "message": "Cash balance is inconsistent across financial statements and notes.",
        "values": {"balance_sheet": 1250.0, "cash_flow": 1270.0, "notes": 1205.0},
        "evidence": [
            {"source": "Balance Sheet", "field": "Cash", "value": 1250.0},
            {"source": "Cash Flow", "field": "Ending Cash", "value": 1270.0},
        ]
    }
    result = member5_finding_adapter(raw)
    assert result["status"] == "exception"  # FAIL -> exception
    assert result["severity"] == "high"  # High -> high
    assert len(result["evidence"]) == 2
    print("[OK] test_member5_finding_adapter_fail")


def test_member5_finding_adapter_unusual():
    raw = {
        "rule_id": "PY001",
        "category": "prior_year",
        "status": "UNUSUAL",
        "severity": "Medium",
        "message": "Cash shows unusual 27.6% movement vs prior year.",
        "values": {"account": "Cash", "current_year": 1250.0, "prior_year": 980.0},
        "evidence": []
    }
    result = member5_finding_adapter(raw)
    assert result["finding_id"] == "F-M5-PY001"
    assert result["module"] == "prior_year_engine"
    assert result["status"] == "warning"  # UNUSUAL -> warning
    assert result["severity"] == "medium"
    assert result["expected"] == 980.0  # prior_year
    assert result["actual"] == 1250.0  # current_year
    assert result["difference"] == 270.0
    print("[OK] test_member5_finding_adapter_unusual")


def test_member5_finding_adapter_review():
    raw = {
        "rule_id": "PY003",
        "category": "prior_year",
        "status": "REVIEW",
        "severity": "Medium",
        "message": "Data unavailable for one or both periods.",
        "values": {"account": "Liabilities", "current_year": None, "prior_year": 10575.0},
        "evidence": []
    }
    result = member5_finding_adapter(raw)
    assert result["status"] == "not_applicable"  # REVIEW -> not_applicable
    print("[OK] test_member5_finding_adapter_review")


def test_ai_output_adapter_grammar():
    raw = {
        "finding_id": "F-AI-GRAM-ABC12345",
        "module": "ai_layer",
        "check": "grammar_review",
        "status": "exception",
        "severity": "low",
        "expected": "Correct spelling",
        "actual": "Typo found: 'recievables'",
        "difference": None,
        "evidence": [{"doc_id": "test.pdf", "page": 8, "table": "Note 7", "row": "Narrative", "period": "FY2025"}],
        "ai_explanation": {
            "original_text": "The bank classifies all trade recievables",
            "flagged_issue": "Spelling: 'recievables' should be 'receivables'",
            "suggested_revision": "The bank classifies all trade receivables",
            "confidence": "high",
            "caveats": "Reviewer to confirm",
            "wp514_target_field": "ai_explanation",
            "label": "SUGGESTED — pending reviewer sign-off"
        }
    }
    result = ai_output_adapter(raw)
    assert result["finding_id"] == "F-AI-GRAM-ABC12345"
    assert result["module"] == "ai_layer"
    assert result["statement"] == "Narrative Disclosure"
    assert result["ai_explanation"] is not None
    assert result["ai_explanation"]["confidence"] == 0.9  # "high" -> 0.9
    assert result["ai_explanation"]["label"] == "SUGGESTED — pending reviewer sign-off"
    print("[OK] test_ai_output_adapter_grammar")


def test_ai_output_adapter_summary():
    raw = {
        "finding_id": "F-AI-SUM-XYZ",
        "module": "ai_layer",
        "check": "overall_review_summary",
        "status": "pass",
        "severity": None,
        "expected": "Summary generated",
        "actual": "Summary prepared",
        "difference": None,
        "evidence": [],
        "ai_explanation": {
            "text": "The review found 2 exceptions...",
            "confidence": "high",
            "caveats": "Reviewer must confirm",
            "wp514_target_field": "review_summary",
            "label": "AI-GENERATED SUMMARY"
        }
    }
    result = ai_output_adapter(raw)
    assert result["statement"] == "Overall Review"
    assert result["severity"] == "low"  # None -> "low"
    print("[OK] test_ai_output_adapter_summary")


def test_confidence_to_float():
    assert _confidence_to_float("high") == 0.9
    assert _confidence_to_float("medium") == 0.6
    assert _confidence_to_float("low") == 0.3
    assert _confidence_to_float(0.85) == 0.85
    assert _confidence_to_float("unknown") == 0.5
    print("[OK] test_confidence_to_float")


def test_merge_all_findings():
    math = [{"finding_id": "m1", "module": "math_engine", "check": "balance_sheet_test", "status": "pass", "severity": "low", "expected": 100, "actual": 100, "difference": 0, "evidence": []}]
    m5 = [
        {"rule_id": "C001", "category": "consistency", "status": "PASS", "severity": "None", "message": "OK", "values": {}, "evidence": []},
        {"rule_id": "PY001", "category": "prior_year", "status": "UNUSUAL", "severity": "Medium", "message": "Spike", "values": {"account": "Cash", "current_year": 100, "prior_year": 50}, "evidence": []}
    ]
    ai = [{"finding_id": "ai1", "module": "ai_layer", "check": "grammar_review", "status": "pass", "severity": "low", "expected": "OK", "actual": "OK", "difference": None, "evidence": []}]

    merged = merge_all_findings(math, m5, ai)
    assert len(merged) == 4  # 1 math + 1 consistency + 1 prior_year + 1 AI
    assert merged[0]["module"] == "math_engine"
    assert merged[1]["module"] == "consistency_engine"
    assert merged[2]["module"] == "prior_year_engine"
    assert merged[3]["module"] == "ai_layer"
    print("[OK] test_merge_all_findings")


def test_compute_summary_kpis():
    findings = [
        {"status": "pass", "severity": "low"},
        {"status": "pass", "severity": "low"},
        {"status": "exception", "severity": "high"},
        {"status": "warning", "severity": "medium"},
        {"status": "not_applicable", "severity": "low"},
    ]
    kpis = compute_summary_kpis(findings)
    assert kpis["total_findings"] == 5
    assert kpis["exceptions"] == 2  # exception + warning
    assert kpis["passes"] == 2
    assert kpis["high_severity"] == 1
    assert kpis["medium_severity"] == 1
    assert kpis["not_applicable"] == 1
    print("[OK] test_compute_summary_kpis")


def test_compute_statement_summaries():
    findings = [
        {"statement": "Balance Sheet", "status": "pass", "severity": "low"},
        {"statement": "Balance Sheet", "status": "exception", "severity": "high"},
        {"statement": "Profit & Loss", "status": "pass", "severity": "low"},
        {"statement": "Cash Flow", "status": "warning", "severity": "medium"},
    ]
    summaries = compute_statement_summaries(findings)
    assert len(summaries) == 3
    bs = next(s for s in summaries if s["statement"] == "Balance Sheet")
    assert bs["checks_performed"] == 2
    assert bs["passed"] == 1
    assert bs["failed"] == 1
    assert bs["overall_status"] == "EXCEPTION"
    cf = next(s for s in summaries if s["statement"] == "Cash Flow")
    assert cf["warnings"] == 1
    assert cf["overall_status"] == "WARNING"
    print("[OK] test_compute_statement_summaries")


def test_evidence_normalization():
    # Test that evidence with non-standard fields gets normalized
    raw = {
        "finding_id": "test",
        "module": "math_engine",
        "check": "balance_sheet_test",
        "status": "pass",
        "severity": "low",
        "expected": 100,
        "actual": 100,
        "difference": 0,
        "evidence": [
            {"source": "Balance Sheet", "field": "Cash", "value": 100},  # Non-standard
        ]
    }
    result = math_finding_adapter(raw)
    assert result["evidence"][0]["doc_id"] == "uploaded.pdf"  # default
    assert result["evidence"][0]["table"] == "Balance Sheet"  # source -> table
    assert result["evidence"][0]["row"] == "Cash"  # field -> row
    print("[OK] test_evidence_normalization")


if __name__ == "__main__":
    test_math_finding_adapter_pass()
    test_math_finding_adapter_exception()
    test_math_finding_adapter_cash_flow()
    test_member5_finding_adapter_pass()
    test_member5_finding_adapter_fail()
    test_member5_finding_adapter_unusual()
    test_member5_finding_adapter_review()
    test_ai_output_adapter_grammar()
    test_ai_output_adapter_summary()
    test_confidence_to_float()
    test_merge_all_findings()
    test_compute_summary_kpis()
    test_compute_statement_summaries()
    test_evidence_normalization()
    print(f"\n{'='*60}")
    print("ALL 14 ADAPTER TESTS PASSED")
    print(f"{'='*60}")

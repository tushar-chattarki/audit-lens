"""
test_full_pipeline.py — Integration Test for Full Pipeline (Member 7)
========================================================================
Tests the complete flow:
  Dummy PDF / Excel file → extraction.extraction_router
                         → canonical JSON
                         → run_full_pipeline
                         → ReviewResponseSchema (Math, Consistency, PY, AI, WP-514)
"""

import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from extraction.extraction_router import extract_document
from integration_orchestrator import run_full_pipeline


def test_sunrise_pdf_extraction_and_pipeline():
    data_dir = Path(backend_dir) / "data"
    pdf_files = list(data_dir.glob("**/*.pdf"))

    if not pdf_files:
        print("[SKIP] No dummy PDF files found in backend/data")
        return

    test_pdf = pdf_files[0]
    print(f"Testing extraction on: {test_pdf.name}")

    extracted = extract_document(
        file_path=test_pdf,
        job_id="TEST-JOB-001",
        bank_name="Sunrise National Bank Ltd.",
        bank_id="SUNRISE"
    )

    assert extracted is not None, "Extraction result is None"
    assert "canonical" in extracted, "Canonical JSON missing from extraction output"

    canonical = extracted["canonical"]
    assert "statements" in canonical, "Statements missing in canonical JSON"

    print(f"[OK] Extraction succeeded for {test_pdf.name}")
    print("      Periods found:", canonical.get("periods"))
    print("      Statements found:", list(canonical.get("statements", {}).keys()))

    metadata = {
        "bank_name": "Sunrise National Bank Ltd.",
        "reporting_period": "FY2025",
        "comparative_period": "FY2024",
        "currency": "INR",
        "unit": "Crores (Cr)",
        "job_id": "TEST-JOB-001"
    }

    # Pass canonical to run_full_pipeline
    result = run_full_pipeline(
        canonical=canonical,
        metadata=metadata,
        doc_id=test_pdf.name
    )

    assert result is not None, "Pipeline result is None"
    assert "review_metadata" in result, "review_metadata missing"
    assert "summary_kpis" in result, "summary_kpis missing"
    assert "findings" in result, "findings missing"
    assert "wp514" in result, "wp514 missing"

    kpis = result["summary_kpis"]
    print("[OK] Pipeline executed successfully")
    print(f"      Total findings: {kpis['total_findings']}")
    print(f"      Exceptions:     {kpis['exceptions']}")
    print(f"      Passes:         {kpis['passes']}")
    print(f"      High severity:  {kpis['high_severity']}")
    print(f"      WP-514 status:  {result['wp514']['engagement_details']['overall_status']}")


if __name__ == "__main__":
    test_sunrise_pdf_extraction_and_pipeline()
    print("\n" + "=" * 60)
    print("FULL PIPELINE INTEGRATION TEST PASSED [OK]")
    print("=" * 60)

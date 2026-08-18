from __future__ import annotations

from pathlib import Path
from typing import Any

from .pdf_extractor import extract_pdf
from .excel_extractor import extract_excel_raw
from .excel_structure import analyze_excel_structure
from .excel_columns import analyze_excel_columns
from .excel_rows import extract_excel_rows
from .excel_canonical_mapper import canonicalize_excel_pipeline


SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXCEL_EXTENSIONS = {".xlsx", ".xlsm"}


def extract_document(
    file_path: str | Path,
    *,
    job_id: str,
    bank_id: str | None = None,
    bank_name: str | None = None,
) -> dict[str, Any]:
    """
    Unified document extraction router.

    Routes:
        PDF  -> PDF extraction + canonicalization
        XLSX -> Excel extraction + canonicalization
        XLSM -> Excel extraction + canonicalization

    Returns:
        {
            "doc_id": str,
            "source_type": str,
            "canonical": dict,
        }
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Input path is not a file: {file_path}"
        )

    extension = file_path.suffix.lower()

    # ==============================================================
    # PDF
    # ==============================================================

    if extension in SUPPORTED_PDF_EXTENSIONS:

        canonical = extract_pdf(
            pdf_path=file_path,
            job_id=job_id,
            bank_id=bank_id,
            bank_name=bank_name,
        )

        return {
            "doc_id": file_path.name,
            "source_type": "pdf",
            "canonical": canonical,
        }

    # ==============================================================
    # EXCEL
    # ==============================================================

    if extension in SUPPORTED_EXCEL_EXTENSIONS:

        # ----------------------------------------------------------
        # 1. Raw extraction
        # ----------------------------------------------------------

        raw_extraction = extract_excel_raw(
            file_path
        )

        # ----------------------------------------------------------
        # 2. Sheet classification + period detection
        # ----------------------------------------------------------

        structure = analyze_excel_structure(
            raw_extraction
        )

        # ----------------------------------------------------------
        # 3. Header / column detection
        # ----------------------------------------------------------

        columns = analyze_excel_columns(
            raw_extraction,
            structure,
        )

        # ----------------------------------------------------------
        # 4. Row extraction
        # ----------------------------------------------------------

        rows = extract_excel_rows(
            raw_extraction,
            columns,
        )

        # ----------------------------------------------------------
        # 5. Canonical mapping
        # ----------------------------------------------------------

        canonical = canonicalize_excel_pipeline(
            raw_extraction=raw_extraction,
            structure=structure,
            rows=rows,
            job_id=job_id,
            bank_id=bank_id,
            bank_name=bank_name,
        )

        return {
            "doc_id": file_path.name,
            "source_type": "xlsx",
            "canonical": canonical,
        }

    # ==============================================================
    # UNSUPPORTED
    # ==============================================================

    raise ValueError(
        f"Unsupported document type: {extension}. "
        "Supported formats are PDF, XLSX and XLSM."
    )
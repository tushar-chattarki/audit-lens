from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

def column_letter(
    cell_ref: str,
) -> str:
    """Extract Excel column letters from a cell reference."""

    return "".join(
        character
        for character in cell_ref
        if character.isalpha()
    )


def row_number_from_cell(
    cell_ref: str,
) -> int | None:
    """Extract the row number from an Excel cell reference."""

    digits = "".join(
        character
        for character in cell_ref
        if character.isdigit()
    )

    if not digits:
        return None

    return int(digits)


def normalize_header(
    value: Any,
) -> str:
    """Normalize a header value for deterministic comparison."""

    if value is None:
        return ""

    return " ".join(
        str(value)
        .strip()
        .lower()
        .split()
    )


def build_cell_lookup(
    sheet: dict[str, Any],
) -> dict[str, Any]:
    """
    Build:
        Excel cell reference -> value
    """

    lookup: dict[str, Any] = {}

    for row in sheet.get(
        "rows",
        [],
    ):

        for cell_ref, value in row.get(
            "cells",
            {},
        ).items():

            lookup[cell_ref] = value

    return lookup


# ---------------------------------------------------------------------------
# Header detection
# ---------------------------------------------------------------------------

LABEL_HEADER_EXACT = {
    "particulars",
    "particular",
    "description",
    "account",
    "accounts",
    "details",
    "item",
    "line item",
    "line_item",
    "nature of item",
    "nature of particulars",
}


LABEL_HEADER_CONTAINS = [
    "particular",
    "description",
    "account name",
    "nature of item",
    "nature of particulars",
    "line item",
]


def _looks_like_label_header(
    value: Any,
) -> bool:
    """Return True when a cell looks like a row-label header."""

    header = normalize_header(value)

    if not header:
        return False

    if header in LABEL_HEADER_EXACT:
        return True

    return any(
        keyword in header
        for keyword in LABEL_HEADER_CONTAINS
    )


def detect_header_row(
    sheet: dict[str, Any],
) -> int | None:
    """
    Detect the main financial-data header row.

    We inspect only the first part of the worksheet because
    the financial header is normally near the top.
    """

    candidate_rows = sheet.get(
        "rows",
        [],
    )[:20]

    for row in candidate_rows:

        for value in row.get(
            "cells",
            {},
        ).values():

            if _looks_like_label_header(
                value
            ):
                return row.get(
                    "row_index"
                )

    return None


def detect_label_column(
    sheet: dict[str, Any],
    header_row: int,
) -> str | None:
    """
    Detect the column containing financial row labels.
    """

    cell_lookup = build_cell_lookup(
        sheet
    )

    for cell_ref, value in cell_lookup.items():

        row_number = row_number_from_cell(
            cell_ref
        )

        if row_number != header_row:
            continue

        if _looks_like_label_header(
            value
        ):
            return column_letter(
                cell_ref
            )

    return None


# ---------------------------------------------------------------------------
# Period column detection
# ---------------------------------------------------------------------------

def detect_period_columns(
    sheet: dict[str, Any],
    period_sources: dict[
        str,
        list[dict[str, Any]],
    ],
) -> dict[str, str]:
    """
    Detect which Excel column contains each financial period.

    We use the period sources already identified by
    excel_structure.py and prefer sources from this sheet.
    """

    period_columns: dict[str, str] = {}

    sheet_name = sheet.get(
        "sheet_name"
    )

    for period, sources in period_sources.items():

        sheet_sources = [
            source
            for source in sources
            if source.get(
                "sheet"
            ) == sheet_name
        ]

        if not sheet_sources:
            continue

        # Prefer the earliest detected source.
        source = sheet_sources[0]

        cell_ref = source.get(
            "cell"
        )

        if not cell_ref:
            continue

        period_columns[period] = (
            column_letter(
                cell_ref
            )
        )

    return period_columns


# ---------------------------------------------------------------------------
# Combined analysis
# ---------------------------------------------------------------------------

def analyze_sheet_columns(
    sheet: dict[str, Any],
    period_sources: dict[
        str,
        list[dict[str, Any]],
    ],
) -> dict[str, Any]:
    """
    Detect structural columns for one worksheet.
    """

    header_row = detect_header_row(
        sheet
    )

    label_column = None

    if header_row is not None:

        label_column = detect_label_column(
            sheet,
            header_row,
        )

    period_columns = detect_period_columns(
        sheet,
        period_sources,
    )

    return {
        "sheet_name": sheet.get(
            "sheet_name"
        ),
        "header_row": header_row,
        "label_column": label_column,
        "period_columns": period_columns,
    }


def analyze_excel_columns(
    raw_extraction: dict[str, Any],
    structure_analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Analyze headers and period columns for all worksheets.
    """

    period_sources = (
        structure_analysis.get(
            "period_sources",
            {},
        )
    )

    classified_sheets = {
        item.get(
            "sheet_name"
        ): item
        for item in structure_analysis.get(
            "sheets",
            [],
        )
    }

    results: list[dict[str, Any]] = []

    for sheet in raw_extraction.get(
        "sheets",
        [],
    ):

        sheet_name = sheet.get(
            "sheet_name"
        )

        sheet_analysis = analyze_sheet_columns(
            sheet,
            period_sources,
        )

        classified = classified_sheets.get(
            sheet_name,
            {},
        )

        sheet_analysis["sheet_type"] = (
            classified.get(
                "sheet_type",
                "other",
            )
        )

        sheet_analysis["confidence"] = (
            classified.get(
                "confidence",
                "low",
            )
        )

        results.append(
            sheet_analysis
        )

    return results
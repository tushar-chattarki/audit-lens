from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Sheet classification
# ---------------------------------------------------------------------------

SHEET_TYPE_KEYWORDS = {
    "balance_sheet": [
        "balance sheet",
        "balance_sheet",
        "statement of financial position",
        "financial position",
    ],
    "profit_and_loss": [
        "profit and loss",
        "profit & loss",
        "profit_loss",
        "p&l",
        "p & l",
        "income statement",
        "statement of profit",
    ],
    "cash_flow": [
        "cash flow",
        "cash_flow",
        "cashflow",
    ],
    "equity": [
        "equity",
        "statement of changes in equity",
        "changes in equity",
    ],
    "notes": [
        "notes",
        "notes to financial statements",
        "financial statement notes",
    ],
    "narrative_notes": [
        "narrative",
        "narratives",
        "commentary",
        "management commentary",
    ],
}


STATEMENT_CONTENT_KEYWORDS = {
    "balance_sheet": [
        "total assets",
        "total liabilities",
        "total equity",
        "assets",
        "liabilities",
    ],
    "profit_and_loss": [
        "revenue",
        "income",
        "expenses",
        "profit before tax",
        "profit after tax",
        "net profit",
        "net loss",
    ],
    "cash_flow": [
        "cash flows from operating activities",
        "cash flows from investing activities",
        "cash flows from financing activities",
        "net cash flow",
        "closing cash",
        "cash and cash equivalents",
    ],
    "equity": [
        "share capital",
        "reserves and surplus",
        "retained earnings",
        "total equity",
    ],
    "notes": [
        "note ",
        "notes to the financial statements",
        "accounting policies",
    ],
}


def _normalize_text(value: Any) -> str:
    """Normalize text for deterministic matching."""

    if value is None:
        return ""

    text = str(value).strip().lower()

    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text)

    return text


def _sheet_content_text(
    sheet: dict[str, Any],
    max_rows: int = 30,
) -> str:
    """
    Build searchable text from the first part of a worksheet.

    The first rows normally contain enough information for sheet
    classification without scanning the entire workbook.
    """

    values: list[str] = []

    for row in sheet.get("rows", [])[:max_rows]:

        for value in row.get("cells", {}).values():

            normalized = _normalize_text(value)

            if normalized:
                values.append(normalized)

    return " ".join(values)


def _keyword_score(
    text: str,
    keywords: list[str],
) -> int:
    """Count classification keyword matches."""

    score = 0

    for keyword in keywords:

        keyword = _normalize_text(keyword)

        if keyword and keyword in text:
            score += 1

    return score


def classify_sheet(
    sheet: dict[str, Any],
) -> dict[str, Any]:
    """
    Classify one worksheet using sheet name and sheet content.
    """

    sheet_name = sheet.get("sheet_name", "")

    normalized_name = _normalize_text(sheet_name)

    content = _sheet_content_text(sheet)

    scores: dict[str, int] = {}

    for sheet_type, keywords in SHEET_TYPE_KEYWORDS.items():

        name_score = _keyword_score(
            normalized_name,
            keywords,
        )

        content_keywords = STATEMENT_CONTENT_KEYWORDS.get(
            sheet_type,
            [],
        )

        content_score = _keyword_score(
            content,
            content_keywords,
        )

        # Sheet name is intentionally stronger than content.
        scores[sheet_type] = (
            name_score * 10
        ) + content_score

    if not scores:

        return {
            "sheet_name": sheet_name,
            "sheet_type": "other",
            "confidence": "low",
            "score": 0,
        }

    best_type = max(
        scores,
        key=scores.get,
    )

    best_score = scores[best_type]

    if best_score == 0:

        sheet_type = "other"
        confidence = "low"

    elif best_score >= 10:

        sheet_type = best_type
        confidence = "high"

    else:

        sheet_type = best_type
        confidence = "medium"

    return {
        "sheet_name": sheet_name,
        "sheet_type": sheet_type,
        "confidence": confidence,
        "score": best_score,
    }


def classify_sheets(
    raw_extraction: dict[str, Any],
) -> list[dict[str, Any]]:
    """Classify every worksheet."""

    return [
        classify_sheet(sheet)
        for sheet in raw_extraction.get(
            "sheets",
            [],
        )
    ]


# ---------------------------------------------------------------------------
# Period detection
# ---------------------------------------------------------------------------

CURRENT_YEAR_PATTERNS = [
    re.compile(
        r"current\s+year\s*\(\s*fy\s*(\d{2,4})\s*\)",
        re.I,
    ),
    re.compile(
        r"current\s+year\s+fy\s*(\d{2,4})",
        re.I,
    ),
    re.compile(
        r"\bfy\s*(\d{2,4})\b",
        re.I,
    ),
]


PREVIOUS_YEAR_PATTERNS = [
    re.compile(
        r"previous\s+year\s*\(\s*fy\s*(\d{2,4})\s*\)",
        re.I,
    ),
    re.compile(
        r"previous\s+year\s+fy\s*(\d{2,4})",
        re.I,
    ),
]


FINANCIAL_YEAR_RANGE_PATTERN = re.compile(
    r"\b(20\d{2})\s*[-/]\s*(\d{2,4})\b"
)


def _normalize_year(year: str) -> str:
    """Convert 26 -> 2026 and preserve four-digit years."""

    year = str(year).strip()

    if len(year) == 2:
        return f"20{year}"

    return year


def _period_id_from_year(
    year: str,
) -> str:
    return f"FY{_normalize_year(year)}"


def detect_period_from_text(
    text: str,
) -> str | None:
    """
    Detect a normalized financial period.

    Examples:
        FY26       -> FY2026
        FY2026     -> FY2026
        2025-26    -> FY2026
        2024-25    -> FY2025
    """

    if not text:
        return None

    text = str(text).strip()

    # Explicit FY notation has priority.
    for pattern in CURRENT_YEAR_PATTERNS:

        match = pattern.search(text)

        if match:
            return _period_id_from_year(
                match.group(1)
            )

    # Financial year range.
    match = FINANCIAL_YEAR_RANGE_PATTERN.search(text)

    if match:

        start_year = int(match.group(1))
        end_part = match.group(2)

        if len(end_part) == 2:

            end_year = int(
                f"{str(start_year)[:2]}{end_part}"
            )

        else:

            end_year = int(end_part)

        return f"FY{end_year}"

    return None


def _extract_periods_from_value(
    value: Any,
) -> list[str]:
    """Extract normalized periods from one cell."""

    if value is None:
        return []

    text = str(value).strip()

    if not text:
        return []

    periods: list[str] = []

    # Current year.
    for pattern in CURRENT_YEAR_PATTERNS:

        match = pattern.search(text)

        if match:

            periods.append(
                _period_id_from_year(
                    match.group(1)
                )
            )

            break

    # Previous year.
    for pattern in PREVIOUS_YEAR_PATTERNS:

        match = pattern.search(text)

        if match:

            periods.append(
                _period_id_from_year(
                    match.group(1)
                )
            )

            break

    # Generic fallback.
    if not periods:

        period = detect_period_from_text(text)

        if period:
            periods.append(period)

    return list(
        dict.fromkeys(periods)
    )


def _is_likely_header_row(
    row: dict[str, Any],
) -> bool:
    """
    Identify rows that are likely to contain period headers.

    This is intentionally heuristic and lightweight.
    """

    values = [
        _normalize_text(value)
        for value in row.get(
            "cells",
            {},
        ).values()
    ]

    text = " ".join(
        value
        for value in values
        if value
    )

    header_keywords = [
        "current year",
        "previous year",
        "current period",
        "previous period",
        "particulars",
        "description",
        "account",
        "fy",
    ]

    return any(
        keyword in text
        for keyword in header_keywords
    )


def _detect_period_sources_in_sheet(
    sheet: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """
    Detect periods within the likely header area of one sheet.

    We first inspect the first 15 rows. This prevents unrelated
    FY references in later notes from dominating period detection.
    """

    period_sources: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    rows = sheet.get(
        "rows",
        [],
    )

    candidate_rows = rows[:15]

    # First pass: likely header rows.
    preferred_rows = [
        row
        for row in candidate_rows
        if _is_likely_header_row(row)
    ]

    # If no obvious header exists, inspect the first 10 rows.
    if not preferred_rows:
        preferred_rows = candidate_rows[:10]

    for row in preferred_rows:

        row_index = row.get(
            "row_index"
        )

        for cell_ref, value in row.get(
            "cells",
            {},
        ).items():

            detected = _extract_periods_from_value(
                value
            )

            for period in detected:

                period_sources.setdefault(
                    period,
                    [],
                ).append(
                    {
                        "sheet": sheet.get(
                            "sheet_name"
                        ),
                        "row_index": row_index,
                        "cell": cell_ref,
                        "value": value,
                    }
                )

    return period_sources


def detect_periods(
    raw_extraction: dict[str, Any],
) -> dict[str, Any]:
    """
    Detect the workbook's financial periods.

    The extractor is designed around the project's two-year
    financial-statement input.

    Period detection is prioritized from likely header rows.
    """

    period_sources: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    # ------------------------------------------------------------------
    # Pass 1: header-focused detection
    # ------------------------------------------------------------------

    for sheet in raw_extraction.get(
        "sheets",
        [],
    ):

        sheet_periods = (
            _detect_period_sources_in_sheet(
                sheet
            )
        )

        for period, sources in sheet_periods.items():

            period_sources.setdefault(
                period,
                [],
            ).extend(sources)

    # ------------------------------------------------------------------
    # Pass 2: fallback
    # ------------------------------------------------------------------
    # Only use this when header-focused detection found fewer than
    # two periods. This keeps the extractor robust without allowing
    # every note/reference to dominate normal detection.
    # ------------------------------------------------------------------

    if len(period_sources) < 2:

        for sheet in raw_extraction.get(
            "sheets",
            [],
        ):

            sheet_name = sheet.get(
                "sheet_name"
            )

            for row in sheet.get(
                "rows",
                [],
            )[:30]:

                row_index = row.get(
                    "row_index"
                )

                for cell_ref, value in row.get(
                    "cells",
                    {},
                ).items():

                    detected = (
                        _extract_periods_from_value(
                            value
                        )
                    )

                    for period in detected:

                        existing = period_sources.setdefault(
                            period,
                            [],
                        )

                        source = {
                            "sheet": sheet_name,
                            "row_index": row_index,
                            "cell": cell_ref,
                            "value": value,
                        }

                        if source not in existing:
                            existing.append(
                                source
                            )

    # Newest first.
    periods = sorted(
        period_sources.keys(),
        reverse=True,
    )

    # MVP supports maximum two periods.
    periods = periods[:2]

    return {
        "periods": periods,
        "period_sources": {
            period: period_sources[period]
            for period in periods
        },
    }


# ---------------------------------------------------------------------------
# Combined structure analysis
# ---------------------------------------------------------------------------

def analyze_excel_structure(
    raw_extraction: dict[str, Any],
) -> dict[str, Any]:
    """
    Perform structural analysis without canonical mapping.
    """

    sheet_classification = classify_sheets(
        raw_extraction
    )

    period_detection = detect_periods(
        raw_extraction
    )

    return {
        "doc_id": raw_extraction.get(
            "doc_id"
        ),
        "source_type": "xlsx",
        "sheets": sheet_classification,
        "periods": period_detection[
            "periods"
        ],
        "period_sources": period_detection[
            "period_sources"
        ],
    }
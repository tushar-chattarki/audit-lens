from __future__ import annotations

import math
import re
from typing import Any


# ---------------------------------------------------------------------------
# Excel reference helpers
# ---------------------------------------------------------------------------

def column_to_number(
    column: str,
) -> int:
    """
    Convert Excel column letters to a 1-based number.

    A  -> 1
    Z  -> 26
    AA -> 27
    """

    result = 0

    for character in column.upper():

        if not character.isalpha():
            continue

        result = (
            result * 26
            + ord(character)
            - ord("A")
            + 1
        )

    return result


def make_cell_reference(
    column: str,
    row_index: int,
) -> str:
    """Create an Excel cell reference."""

    return f"{column}{row_index}"


# ---------------------------------------------------------------------------
# Value normalization
# ---------------------------------------------------------------------------

def normalize_label(
    value: Any,
) -> str:
    """
    Normalize an Excel row label.

    The original value is preserved separately through the raw
    extraction layer.
    """

    if value is None:
        return ""

    text = str(value).strip()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def is_blank(
    value: Any,
) -> bool:
    """Return True if a cell is effectively blank."""

    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    return False


def normalize_numeric_value(
    value: Any,
) -> Any:
    """
    Normalize numeric Excel values.

    Missing values remain None.

    They are NEVER converted to zero.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):

        if (
            isinstance(value, float)
            and math.isnan(value)
        ):
            return None

        return value

    if isinstance(value, str):

        text = value.strip()

        if not text:
            return None

        # Remove thousands separators.
        cleaned = text.replace(
            ",",
            "",
        )

        try:

            number = float(cleaned)

            if math.isnan(number):
                return None

            if number.is_integer():
                return int(number)

            return number

        except ValueError:

            # Preserve non-numeric text.
            return value

    return value


# ---------------------------------------------------------------------------
# Row extraction
# ---------------------------------------------------------------------------

def extract_rows_from_sheet(
    sheet: dict[str, Any],
    column_analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Extract financial rows from one worksheet.

    This remains an intermediate representation.
    It is NOT canonical JSON.

    Example:

        {
            "sheet_name": "Balance Sheet",
            "sheet_type": "balance_sheet",
            "row_index": 36,
            "label": "Equity Share Capital",
            "values": {
                "FY2026": 9500,
                "FY2025": 9500
            },
            "cells": {
                "FY2026": "C36",
                "FY2025": "D36"
            }
        }
    """

    header_row = column_analysis.get(
        "header_row"
    )

    label_column = column_analysis.get(
        "label_column"
    )

    period_columns = column_analysis.get(
        "period_columns",
        {},
    )

    if header_row is None:
        return []

    if not label_column:
        return []

    extracted_rows: list[
        dict[str, Any]
    ] = []

    for row in sheet.get(
        "rows",
        [],
    ):

        row_index = row.get(
            "row_index"
        )

        if row_index is None:
            continue

        # Skip header and rows before header.
        if row_index <= header_row:
            continue

        cells = row.get(
            "cells",
            {}
        )

        label_cell = make_cell_reference(
            label_column,
            row_index,
        )

        label_value = cells.get(
            label_cell
        )

        # Ignore blank-label rows.
        if is_blank(label_value):
            continue

        label = normalize_label(
            label_value
        )

        values: dict[
            str,
            Any
        ] = {}

        cell_references: dict[
            str,
            str
        ] = {}

        for period, column in (
            period_columns.items()
        ):

            cell_ref = make_cell_reference(
                column,
                row_index,
            )

            value = cells.get(
                cell_ref
            )

            values[period] = (
                normalize_numeric_value(
                    value
                )
            )

            cell_references[
                period
            ] = cell_ref

        extracted_rows.append(
            {
                "sheet_name": sheet.get(
                    "sheet_name"
                ),
                "sheet_type": column_analysis.get(
                    "sheet_type",
                    "other",
                ),
                "row_index": row_index,
                "label": label,
                "values": values,
                "cells": cell_references,
            }
        )

    return extracted_rows


def extract_excel_rows(
    raw_extraction: dict[str, Any],
    column_analysis: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Extract rows from all recognized financial worksheets.
    """

    analysis_by_sheet = {
        item.get(
            "sheet_name"
        ): item
        for item in column_analysis
    }

    results: list[
        dict[str, Any]
    ] = []

    for sheet in raw_extraction.get(
        "sheets",
        [],
    ):

        sheet_name = sheet.get(
            "sheet_name"
        )

        analysis = analysis_by_sheet.get(
            sheet_name
        )

        if not analysis:
            continue

        sheet_type = analysis.get(
            "sheet_type",
            "other",
        )

        # Ignore non-financial worksheets.
        if sheet_type == "other":
            continue

        rows = extract_rows_from_sheet(
            sheet,
            analysis,
        )

        results.extend(rows)

    return results
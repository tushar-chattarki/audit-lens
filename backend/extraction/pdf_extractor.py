from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import fitz

from .mappings import (
    CanonicalTarget,
    infer_row_type,
    is_parent_label,
    label_to_key,
    map_label,
    section_from_label,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_JSON_PATH = PROJECT_ROOT / "backend" / "data" / "example.json"


PERIOD_RANGE_PATTERN = re.compile(
    r"FY\s*(20\d{2})\s*-\s*(\d{2})",
    re.IGNORECASE,
)

PERIOD_SHORT_PATTERN = re.compile(
    r"FY\s*(\d{2})",
    re.IGNORECASE,
)

PERIOD_LONG_PATTERN = re.compile(
    r"FY\s*(20\d{2})(?!\s*-)",
    re.IGNORECASE,
)

NOTE_VALUE_PATTERN = re.compile(
    r"Rs\.\s*([\d,]+)\s*lakhs.*?"
    r"Previous Year:\s*Rs\.\s*([\d,]+)\s*lakhs",
    re.IGNORECASE | re.DOTALL,
)

NOTE_TOTAL_PATTERN = re.compile(
    r"^\s*total\s*\(\s*note\s*(\d+)\s*\)\s*$",
    re.IGNORECASE,
)


# ============================================================================
# Period handling
# ============================================================================

def load_canonical_template() -> dict[str, Any]:
    with EXAMPLE_JSON_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_period(
    text: str,
    column_position: int | None = None,
) -> str | None:
    range_match = PERIOD_RANGE_PATTERN.search(text)
    if range_match:
        return f"FY{range_match.group(1)}"

    long_match = PERIOD_LONG_PATTERN.search(text)
    if long_match:
        return f"FY{long_match.group(1)}"

    short_match = PERIOD_SHORT_PATTERN.search(text)
    if short_match:
        end_year = 2000 + int(short_match.group(1))
        return f"FY{end_year - 1}"

    lowered = text.lower()

    if "current year" in lowered:
        return "FY2025"

    if "previous year" in lowered:
        return "FY2024"

    if column_position == 0:
        return "FY2025"

    if column_position == 1:
        return "FY2024"

    return None


def detect_periods(text: str) -> list[str]:
    periods: list[str] = []

    for match in PERIOD_RANGE_PATTERN.finditer(text):
        period = f"FY{match.group(1)}"
        if period not in periods:
            periods.append(period)

    for match in PERIOD_LONG_PATTERN.finditer(text):
        period = f"FY{match.group(1)}"
        if period not in periods:
            periods.append(period)

    return periods[:2]


# ============================================================================
# Units / numbers
# ============================================================================

def detect_unit(text: str) -> str:
    lowered = text.lower()

    if "lakhs" in lowered or "lakh" in lowered:
        return "lakh"

    if "crores" in lowered or "crore" in lowered:
        return "crore"

    return "lakh"


def convert_to_lakh(
    value: float | None,
    source_unit: str,
) -> float | None:
    """
    Convert an extracted value to the canonical lakh unit.

    The canonical pipeline currently uses INR lakh.
    """

    if value is None:
        return None

    if source_unit == "lakh":
        return value

    if source_unit == "crore":
        return value * 100

    return value


def parse_number(value: Any) -> float | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text or text == "-":
        return None

    text = text.replace(",", "")
    text = text.replace("₹", "")
    text = text.replace("$", "")
    text = text.replace("€", "")
    text = text.replace("£", "")
    text = text.strip()

    # Financial statements commonly use brackets for negative values:
    # (4,800) -> -4800
    if text.startswith("(") and text.endswith(")"):
        text = f"-{text[1:-1]}"

    text = re.sub(r"[^\d.\-]", "", text)

    if not text or text == "-":
        return None

    return float(text)


# ============================================================================
# Evidence
# ============================================================================

def make_evidence(
    doc_id: str,
    page: int,
    table: str,
    row: str,
    period: str,
) -> dict[str, Any]:
    return {
        "doc_id": doc_id,
        "page": page,
        "table": table,
        "row": row,
        "period": period,
    }


def make_value(
    value: float,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "value": value,
        "evidence": evidence,
    }


def missing_value() -> dict[str, Any]:
    return {
        "value": None,
        "reason": "not_found",
        "evidence": None,
    }


# ============================================================================
# Statement / table detection
# ============================================================================

def detect_statement(page_text: str) -> str | None:
    lowered = page_text.lower()
    stripped = lowered.lstrip()

    if (
        stripped.startswith("schedules forming part")
        or re.match(r"schedule\s+\d+", stripped)
    ):
        return None

    if "balance sheet" in lowered:
        return "balance_sheet"

    if "profit and loss" in lowered:
        return "profit_and_loss"

    if "cash flow statement" in lowered:
        return "cash_flow"

    return None


def table_name_for_page(
    page_text: str,
    table_index: int,
) -> str:
    lowered = page_text.lower().lstrip()

    if (
        lowered.startswith("schedules forming part")
        or re.match(r"schedule\s+\d+", lowered)
    ):
        return f"Schedule Table {table_index}"

    statement = detect_statement(page_text)

    if statement == "balance_sheet":
        return "Balance Sheet"

    if statement == "profit_and_loss":
        return "Profit and Loss"

    if statement == "cash_flow":
        return "Cash Flow"

    if "schedule" in page_text.lower():
        return f"Schedule Table {table_index}"

    return f"Table {table_index}"


def period_columns(header: list[str]) -> dict[str, int]:
    columns: dict[str, int] = {}
    value_position = 0

    for index, cell in enumerate(header):
        period = normalize_period(
            cell,
            column_position=value_position,
        )

        if period and index > 0:
            columns[period] = index
            value_position += 1

    return columns


# ============================================================================
# Notes
# ============================================================================

def target_to_dict(
    target: CanonicalTarget | None,
) -> dict[str, Any] | None:
    if target is None:
        return None

    return {
        "statement": target.statement,
        "path": list(target.path),
    }

def extract_note_number(label: str) -> str | None:
    match = NOTE_TOTAL_PATTERN.match(label.strip())

    if match:
        return match.group(1)

    return None


def table_note_numbers(rows: list[list[Any]]) -> list[str]:
    note_numbers: list[str] = []

    for row in rows[1:]:
        if not row:
            continue

        label = str(row[0] or "").strip()

        note_number = extract_note_number(label)

        if note_number and note_number not in note_numbers:
            note_numbers.append(note_number)

    return note_numbers

def assign_note_numbers(
    rows: list[list[Any]],
) -> dict[int, str]:
    """
    Assign each row in a note table to its Note number.

    Example:

        Cash on Hand
        Balances with Banks
        Total (Note 3)

    All three rows belong to Note 3.
    """

    assignments: dict[int, str] = {}

    current_start = 1

    for index in range(1, len(rows)):
        row = rows[index]

        if not row:
            continue

        label = str(row[0] or "").strip()

        note_number = extract_note_number(label)

        if note_number:
            for row_index in range(
                current_start,
                index + 1,
            ):
                assignments[row_index] = note_number

            current_start = index + 1

    return assignments


def extract_notes(
    page_text: str,
    doc_id: str,
    page_number: int,
) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []

    note_blocks = re.findall(
        r"(\d+)\.\s+([^:]+):\s+(.*?)(?=\n\d+\.|$)",
        page_text,
        re.DOTALL,
    )

    for note_number, title, body in note_blocks:
        values: dict[str, float | None] = {}

        match = NOTE_VALUE_PATTERN.search(body)

        if match:
            values = {
                "FY2025": parse_number(match.group(1)),
                "FY2024": parse_number(match.group(2)),
            }

        row = title.strip()

        notes.append(
            {
                "doc_id": doc_id,
                "page": page_number,
                "table": f"Note {note_number}",
                "row": row,
                "text": re.sub(
                    r"\s+",
                    " ",
                    body,
                ).strip(),
                "period_values": values,
                "canonical_target": target_to_dict(
                    map_label(row, "notes")
                ),
            }
        )

    return notes


# ============================================================================
# Raw PDF extraction
# ============================================================================

def is_notes_disclosure_heading(page_text: str) -> bool:
    text = " ".join(page_text.lower().split())

    return (
        "notes forming part of the financial statements" in text
        or "notes to the financial statements" in text
    )

def extract_raw_pdf(
    pdf_path: str | Path,
) -> dict[str, Any]:
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    document = fitz.open(pdf_path)

    raw: dict[str, Any] = {
        "doc_id": pdf_path.name,
        "source_unit": "crore",
        "periods": [],
        "rows": [],
        "issues": [],
        "notes": [],
        "disclosures": [],
    }

    try:
        full_text = "\n".join(
            page.get_text("text")
            for page in document
        )

        raw["periods"] = detect_periods(full_text)
        raw["source_unit"] = detect_unit(full_text)

        in_disclosures = False

        for page_index, page in enumerate(document):
            page_number = page_index + 1
            page_text = page.get_text("text")
            page_statement = detect_statement(page_text)

            page_text_lower = page_text.lower()

            if is_notes_disclosure_heading(page_text):
                in_disclosures = True

            if in_disclosures and page_text.strip():
                raw["disclosures"].append(
                    {
                        "doc_id": raw["doc_id"],
                        "page": page_number,
                        "section": "notes_to_financial_statements",
                        "text": page_text.strip(),
                    }
                )

            if "notes forming part" in page_text.lower():
                raw["notes"].extend(
                    extract_notes(
                        page_text,
                        raw["doc_id"],
                        page_number,
                    )
                )

            try:
                tables = page.find_tables()
            except Exception as exc:
                raw["issues"].append(
                    {
                        "page": page_number,
                        "issue": f"table_extraction_failed: {exc}",
                    }
                )
                continue

            if not tables.tables and page_statement:
                raw["issues"].append(
                    {
                        "page": page_number,
                        "issue": "no_tables_detected_for_statement_page",
                    }
                )

            for table_index, table in enumerate(
                tables.tables,
                start=1,
            ):
                rows = table.extract()

                if not rows:
                    raw["issues"].append(
                        {
                            "page": page_number,
                            "table": table_index,
                            "issue": "empty_table_detected",
                        }
                    )
                    continue

                # --------------------------------------------------------------
                # Detect whether this table contains financial statement notes
                # --------------------------------------------------------------
                note_numbers = table_note_numbers(rows)
                is_note_table = bool(note_numbers)

                note_assignments = (
                    assign_note_numbers(rows)
                    if is_note_table
                    else {}
                )

                header = [
                    str(cell or "").strip()
                    for cell in rows[0]
                ]

                columns = period_columns(header)

                if not columns:
                    raw["issues"].append(
                        {
                            "page": page_number,
                            "table": table_index,
                            "issue": "no_period_columns_detected",
                        }
                    )
                    continue

                table_name = table_name_for_page(
                    page_text,
                    table_index,
                )

                # A table containing "Total (Note N)" markers is treated
                # as a Notes table even if the page itself says "Balance Sheet".
                table_statement = "notes" if is_note_table else page_statement

                current_section: str | None = None
                current_note_number: str | None = None

                for row_index, row in enumerate(rows[1:], start=1):
                    cells = [
                        str(cell or "").strip()
                        for cell in row
                    ]

                    label = cells[0] if cells else ""

                    if not label:
                        continue

                    row_note_number = note_assignments.get(row_index)

                    row_values: dict[str, float | None] = {}

                    for period, column_index in columns.items():
                        raw_value = (
                            cells[column_index]
                            if column_index < len(cells)
                            else ""
                        )

                        row_values[period] = parse_number(
                            raw_value
                        )

                    # ------------------------------------------------------
                    # Section detection
                    # ------------------------------------------------------

                    detected_section = section_from_label(
                        label,
                        table_statement,
                    )

                    if detected_section is not None:
                        current_section = detected_section

                    # ------------------------------------------------------
                    # Known semantic mapping
                    # ------------------------------------------------------

                    if table_statement == "notes":
                        canonical_target = None
                    else:
                        canonical_target = map_label(
                            label,
                            table_statement,
                        )

                    # ------------------------------------------------------
                    # Row classification
                    # ------------------------------------------------------

                    has_numeric_value = any(
                        value is not None
                        for value in row_values.values()
                    )

                    row_type = infer_row_type(
                        label,
                        has_values=has_numeric_value,
                    )

                    # ------------------------------------------------------
                    # Raw row
                    # ------------------------------------------------------

                    raw["rows"].append(
                        {
                            "doc_id": raw["doc_id"],
                            "page": page_number,
                            "table": table_name,
                            "statement": table_statement,
                            "section": current_section,
                            "note_number": row_note_number,
                            "row": label,
                            "period_values": row_values,
                            "is_parent": is_parent_label(label),
                            "row_type": row_type,
                            "canonical_target": target_to_dict(
                                canonical_target
                            ),
                        }
                    )

        return raw

    finally:
        document.close()


# ============================================================================
# Canonical template handling
# ============================================================================

def template_with_metadata(
    template: dict[str, Any],
    job_id: str,
    bank_id: str | None,
    bank_name: str | None,
    periods: list[str],
) -> dict[str, Any]:

    canonical = copy.deepcopy(template)

    canonical["job_id"] = job_id
    canonical["bank_id"] = bank_id
    canonical["bank_name"] = bank_name

    canonical["currency"] = "INR"
    canonical["unit"] = "lakh"
    canonical["periods"] = periods

    reset_values(canonical["statements"])

    return canonical


def reset_values(node: Any) -> None:
    if not isinstance(node, dict):
        return

    # --------------------------------------------------------------
    # Financial value node
    # --------------------------------------------------------------
    if "value" in node and "evidence" in node:
        row_type = node.get("row_type")
        source_label = node.get("source_label")
        canonical_key = node.get("canonical_key")

        node.clear()

        if row_type is not None:
            node["row_type"] = row_type

        if source_label is not None:
            node["source_label"] = source_label

        if canonical_key is not None:
            node["canonical_key"] = canonical_key

        node.update(missing_value())
        return

    # --------------------------------------------------------------
    # Narrative/text node
    # --------------------------------------------------------------
    if "text" in node and "evidence" in node:
        node["text"] = None
        node["evidence"] = None
        return

    # --------------------------------------------------------------
    # Recurse into nested structures
    # --------------------------------------------------------------
    for value in node.values():
        reset_values(value)


# ============================================================================
# Canonical target creation
# ============================================================================

def build_dynamic_target(
    row: dict[str, Any],
) -> CanonicalTarget | None:
    """
    Create a canonical target for a legitimate unmapped row.

    Existing semantic mappings always take priority.

    If a section is known:
        statement.section.account

    If the section is unknown:
        statement.additional_items.account

    This preserves unknown rows without polluting the
    main canonical hierarchy.
    """

    statement = row.get("statement")
    section = row.get("section")
    label = row.get("row", "")

    if not statement:
        return None

    if row.get("row_type") == "heading":
        return None

    account_key = label_to_key(label)

    if not account_key:
        return None

    if statement == "notes":
        note_number = row.get("note_number")

        if not note_number:
            return None

        return CanonicalTarget(
            statement="notes",
            path=(
                "schedules",
                f"note_{note_number}",
                account_key,
            ),
        )

    # Known section
    if section:
        return CanonicalTarget(
            statement=statement,
            path=(section, account_key),
        )

    # Unknown section
    if statement in {
        "balance_sheet",
        "profit_and_loss",
    }:
        return CanonicalTarget(
            statement=statement,
            path=("additional_items", account_key),
        )

    if statement == "cash_flow":
        return CanonicalTarget(
            statement=statement,
            path=("operating_activities", "additional_items", account_key),
        )

    if statement == "equity":
        return CanonicalTarget(
            statement=statement,
            path=("additional_items", account_key),
        )

    return None

# ============================================================================
# Canonical value insertion
# ============================================================================

def ensure_canonical_node(
    canonical: dict[str, Any],
    target: CanonicalTarget,
    row_type: str,
) -> dict[str, Any] | None:
    """
    Ensure that a canonical account node exists.

    Existing template keys are preserved.
    New legitimate rows are added dynamically.
    """

    statement_node = canonical["statements"].get(
        target.statement
    )

    if statement_node is None:
        return None

    node = statement_node

    for key in target.path:
        if not isinstance(node, dict):
            return None

        if key not in node:
            node[key] = {
                "row_type": row_type,
            }

        node = node[key]

    if not isinstance(node, dict):
        return None

    # Existing rows from the old template may not have row_type.
    # Add it without changing any existing key.
    node.setdefault("row_type", row_type)

    return node


def set_canonical_value(
    canonical: dict[str, Any],
    target: CanonicalTarget,
    period: str,
    value: float,
    evidence: dict[str, Any],
    row_type: str,
) -> None:
    node = ensure_canonical_node(
        canonical=canonical,
        target=target,
        row_type=row_type,
    )

    if node is None:
        return

    node[period] = make_value(
        value,
        evidence,
    )

def reorder_canonical_to_source_order(
    canonical: dict[str, Any],
    raw: dict[str, Any],
) -> None:
    """
    Reorder canonical statement fields according to the order
    in which rows appeared in the source document.

    Existing template fields that were not present in the source
    are preserved and placed after the source-derived fields.

    This changes ordering only. It does not change values,
    mappings, evidence, or schema structure.
    """

    statement_order: dict[str, list[tuple[str, ...]]] = {}

    # --------------------------------------------------------------
    # 1. Collect canonical paths in source-document order.
    # --------------------------------------------------------------

    for row in raw["rows"]:
        target_data = row.get("canonical_target")

        if target_data is not None:
            statement = target_data.get("statement")
            path = tuple(target_data.get("path", []))

        else:
            target = build_dynamic_target(row)

            if target is None:
                continue

            statement = target.statement
            path = tuple(target.path)

        if not statement or not path:
            continue

        statement_order.setdefault(
            statement,
            [],
        ).append(path)

    # --------------------------------------------------------------
    # 2. Reorder each statement recursively.
    # --------------------------------------------------------------

    for statement, paths in statement_order.items():
        statement_node = canonical["statements"].get(statement)

        if not isinstance(statement_node, dict):
            continue

        # Rank every path component according to its first
        # occurrence in the source document.
        #
        # Example:
        #
        # assets.cash
        # assets.investments
        # assets.advances
        #
        # becomes:
        #
        # assets -> cash
        #          investments
        #          advances
        path_ranks: dict[tuple[str, ...], int] = {}

        for index, path in enumerate(paths):
            for depth in range(1, len(path) + 1):
                prefix = path[:depth]

                if prefix not in path_ranks:
                    path_ranks[prefix] = index

        reorder_dict_recursively(
            node=statement_node,
            current_path=(),
            path_ranks=path_ranks,
        )


def reorder_dict_recursively(
    node: dict[str, Any],
    current_path: tuple[str, ...],
    path_ranks: dict[tuple[str, ...], int],
) -> None:
    """
    Recursively reorder a canonical dictionary according to
    source-document path order.

    Fields that were not present in the source retain their
    existing order after all source-derived fields.
    """

    original_items = list(node.items())

    ranked_items: list[tuple[int, int, str, Any]] = []
    unranked_items: list[tuple[int, str, Any]] = []

    for original_index, (key, value) in enumerate(original_items):
        child_path = current_path + (key,)

        rank = path_ranks.get(child_path)

        if rank is not None:
            ranked_items.append(
                (
                    rank,
                    original_index,
                    key,
                    value,
                )
            )
        else:
            unranked_items.append(
                (
                    original_index,
                    key,
                    value,
                )
            )

    ranked_items.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    reordered: dict[str, Any] = {}

    # Source-derived fields first.
    for _, _, key, value in ranked_items:
        reordered[key] = value

    # Template-only fields afterward.
    for _, key, value in unranked_items:
        reordered[key] = value

    node.clear()
    node.update(reordered)

    # --------------------------------------------------------------
    # Recursively reorder nested dictionaries.
    # --------------------------------------------------------------

    for key, value in node.items():
        if isinstance(value, dict):
            reorder_dict_recursively(
                node=value,
                current_path=current_path + (key,),
                path_ranks=path_ranks,
            )


# ============================================================================
# Canonicalization
# ============================================================================

def canonicalize_raw_extraction(
    raw: dict[str, Any],
    job_id: str,
    bank_id: str | None = None,
    bank_name: str | None = None,
) -> dict[str, Any]:
    template = load_canonical_template()

    # Keep the periods supported by the current canonical template.
    #
    # This preserves your current 2-year schema while still allowing
    # the extraction layer to detect other periods in raw data.
    periods = [
        period
        for period in template["periods"]
        if period in raw["periods"]
    ]

    canonical = template_with_metadata(
        template,
        job_id,
        bank_id,
        bank_name,
        periods,
    )

    source_unit = raw["source_unit"]

    for row in raw["rows"]:
        # --------------------------------------------------------------
        # 1. Prefer the existing semantic mapping.
        # --------------------------------------------------------------

        target_data = row.get("canonical_target")

        if target_data is not None:
            target = CanonicalTarget(
                statement=target_data["statement"],
                path=tuple(target_data["path"]),
            )

        else:
            # ----------------------------------------------------------
            # 2. Unknown row:
            #    use statement + section + normalized row name.
            # ----------------------------------------------------------

            target = build_dynamic_target(row)

        if target is None:
            # Heading or structurally unusable row.
            continue

        # Safety check: never place a row into a different statement
        # from the one detected during extraction.
        if row.get("statement") != target.statement:
            continue

        row_type = row.get(
            "row_type",
            "line_item",
        )

        for period, raw_value in row[
            "period_values"
        ].items():

            # Only populate periods supported by the canonical schema.
            if period not in periods:
                continue

            converted = convert_to_lakh(
                raw_value,
                source_unit,
            )

            if converted is None:
                continue

            evidence = make_evidence(
                doc_id=row["doc_id"],
                page=row["page"],
                table=row["table"],
                row=row["row"],
                period=period,
            )

            set_canonical_value(
                canonical=canonical,
                target=target,
                period=period,
                value=converted,
                evidence=evidence,
                row_type=row_type,
            )

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------

    for note in raw["notes"]:
        target_data = note.get("canonical_target")

        if target_data is None:
            continue

        target = CanonicalTarget(
            statement=target_data["statement"],
            path=tuple(target_data["path"]),
        )

        for period, raw_value in note[
            "period_values"
        ].items():

            if period not in periods:
                continue

            converted = convert_to_lakh(
                raw_value,
                source_unit,
            )

            if converted is None:
                continue

            evidence = make_evidence(
                doc_id=note["doc_id"],
                page=note["page"],
                table=note["table"],
                row=note["row"],
                period=period,
            )

            set_canonical_value(
                canonical=canonical,
                target=target,
                period=period,
                value=converted,
                evidence=evidence,
                row_type="line_item",
            )

    # ------------------------------------------------------------------
    # Disclosures
    # ------------------------------------------------------------------

    canonical["statements"]["notes"]["disclosures"] = [
        {
            "section": disclosure.get("section"),
            "text": disclosure.get("text"),
            "evidence": {
                "doc_id": disclosure.get("doc_id"),
                "page": disclosure.get("page"),
            },
        }
        for disclosure in raw.get("disclosures", [])
    ]

    reorder_canonical_to_source_order(
        canonical=canonical,
        raw=raw,
    )

    return canonical


# ============================================================================
# Public extraction function
# ============================================================================

def extract_pdf(
    pdf_path: str | Path,
    job_id: str,
    bank_id: str | None = None,
    bank_name: str | None = None,
) -> dict[str, Any]:
    raw = extract_raw_pdf(pdf_path)

    return canonicalize_raw_extraction(
        raw,
        job_id,
        bank_id,
        bank_name,
    )
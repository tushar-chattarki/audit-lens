from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .mappings import (
    CanonicalTarget,
    infer_row_type,
    is_parent_label,
    map_label,
    section_from_label,
)


# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

def normalize_dynamic_key(label: str) -> str:
    """
    Convert an unmapped Excel label into a deterministic snake_case key.

    Example:
        "Other Financial Assets" -> "other_financial_assets"
    """

    value = label.strip().lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )

    value = re.sub(
        r"_+",
        "_",
        value,
    )

    return value.strip("_")


def make_excel_evidence(
    *,
    doc_id: str,
    sheet_name: str,
    cell: str,
    row: str,
    period: str,
) -> dict[str, Any]:
    """
    Evidence structure for Excel.

    PDF:
        page / table

    Excel:
        sheet / cell
    """

    return {
        "doc_id": doc_id,
        "sheet": sheet_name,
        "cell": cell,
        "row": row,
        "period": period,
    }


# ---------------------------------------------------------------------------
# Row classification
# ---------------------------------------------------------------------------

def classify_row(
    row: dict[str, Any],
) -> str:
    """
    Determine the row type using the existing mapping logic.
    """

    label = str(
        row.get("label", "")
    ).strip()

    values = row.get(
        "values",
        {},
    )

    has_values = any(
        value is not None
        for value in values.values()
    )

    return infer_row_type(
        label,
        has_values=has_values,
    )


def is_control_row(
    label: str,
) -> bool:
    """
    Identify workbook control/check rows that should not become
    canonical financial accounts.
    """

    lowered = label.strip().lower()

    return lowered.startswith(
        (
            "tie-out check:",
            "cross-check",
            "check:",
        )
    )


def is_structural_row(
    label: str,
    row_type: str,
) -> bool:
    """
    Identify rows that represent headings/structure rather than
    actual financial values.
    """

    if row_type in {
        "section",
        "subsection",
        "header",
        "narrative",
        "check",
    }:
        return True

    if is_parent_label(label):
        return True

    if is_control_row(label):
        return True

    return False


# ---------------------------------------------------------------------------
# Dynamic canonical structure
# ---------------------------------------------------------------------------

def create_empty_canonical(
    *,
    periods: list[str],
    job_id: str | None,
    bank_id: str | None,
    bank_name: str | None,
    currency: str = "INR",
    unit: str = "lakh",
) -> dict[str, Any]:
    """
    Create the canonical root.

    IMPORTANT:
    This does NOT copy example(5).json.

    Only metadata and the statements container are created initially.
    """

    return {
        "job_id": job_id,
        "bank_id": bank_id,
        "bank_name": bank_name,
        "currency": currency,
        "unit": unit,
        "periods": list(periods),
        "statements": {},
    }


def ensure_statement(
    canonical: dict[str, Any],
    statement: str,
) -> dict[str, Any]:
    """
    Create a statement only when the Excel workbook actually contains
    data belonging to that statement.
    """

    statements = canonical["statements"]

    if statement not in statements:
        statements[statement] = {}

    return statements[statement]


def ensure_path(
    statement_node: dict[str, Any],
    path: tuple[str, ...],
) -> dict[str, Any]:
    """
    Create only the canonical hierarchy required by an actual
    extracted Excel row.

    Example:

        path = ("assets", "cash_and_cash_equivalents")

    creates:

        balance_sheet
            └── assets
                └── cash_and_cash_equivalents
    """

    current = statement_node

    for part in path:

        if part not in current:
            current[part] = {}

        if not isinstance(
            current[part],
            dict,
        ):
            raise TypeError(
                f"Canonical path conflict at '{part}'."
            )

        current = current[part]

    return current


# ---------------------------------------------------------------------------
# Dynamic target for genuinely unmapped rows
# ---------------------------------------------------------------------------

def build_dynamic_target(
    row: dict[str, Any],
) -> CanonicalTarget | None:
    """
    Build an additional_items target for a legitimate financial row
    that has no explicit mapping.

    This is deliberately conservative.
    """

    label = str(
        row.get("label", "")
    ).strip()

    statement = row.get(
        "sheet_type"
    )

    row_type = row.get(
        "row_type"
    )

    if not label or not statement:
        return None

    if is_structural_row(
        label,
        row_type,
    ):
        return None

    key = normalize_dynamic_key(
        label
    )

    if not key:
        return None

    section = section_from_label(
        label,
        statement,
    )

    if section:

        path = (
            section,
            "additional_items",
            key,
        )

    else:

        path = (
            "additional_items",
            key,
        )

    return CanonicalTarget(
        statement=statement,
        path=path,
    )


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------

def resolve_known_target(
    canonical: dict[str, Any],
    target: CanonicalTarget,
) -> dict[str, Any] | None:
    """
    Resolve an existing target.

    This is primarily useful for diagnostics.

    It NEVER creates anything.
    """

    statements = canonical.get(
        "statements",
        {},
    )

    statement_node = statements.get(
        target.statement
    )

    if not isinstance(
        statement_node,
        dict,
    ):
        return None

    current: Any = statement_node

    for part in target.path:

        if not isinstance(
            current,
            dict,
        ):
            return None

        current = current.get(
            part
        )

        if current is None:
            return None

    if not isinstance(
        current,
        dict,
    ):
        return None

    return current


def create_target(
    canonical: dict[str, Any],
    target: CanonicalTarget,
) -> dict[str, Any]:
    """
    Create the target dynamically under statements.

    Example:

        target.statement = "balance_sheet"
        target.path = ("assets", "cash_and_cash_equivalents")

    becomes:

        canonical["statements"]
            ["balance_sheet"]
            ["assets"]
            ["cash_and_cash_equivalents"]
    """

    statement_node = ensure_statement(
        canonical,
        target.statement,
    )

    return ensure_path(
        statement_node,
        target.path,
    )


# ---------------------------------------------------------------------------
# Value writing
# ---------------------------------------------------------------------------

def write_period_value(
    node: dict[str, Any],
    *,
    period: str,
    value: Any,
    evidence: dict[str, Any],
) -> None:
    """
    Write a canonical period value.

    The structure intentionally matches the existing canonical contract:

        "FY2026": {
            "value": ...,
            "evidence": {...}
        }
    """

    node[period] = {
        "value": value,
        "evidence": evidence,
    }


# ---------------------------------------------------------------------------
# Main canonical mapper
# ---------------------------------------------------------------------------

def canonicalize_excel_rows(
    raw_extraction: dict[str, Any],
    structure: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    bank_id: str | None = None,
    bank_name: str | None = None,
    job_id: str | None = None,
) -> dict[str, Any]:
    """
    Convert extracted Excel rows into the canonical financial structure.

    IMPORTANT DESIGN RULES
    ----------------------
    1. The workbook is the source of truth for available data.
    2. example(5).json is NOT copied.
    3. Only fields represented by actual Excel rows are created.
    4. Existing mapping functions determine canonical names.
    5. Excel evidence uses sheet + cell.
    6. Missing values remain absent; they are never converted to zero.
    7. Notes are handled separately.
    """

    periods = list(
        structure.get(
            "periods",
            [],
        )
    )

    canonical = create_empty_canonical(
        periods=periods,
        job_id=job_id,
        bank_id=bank_id,
        bank_name=bank_name,
    )

    doc_id = raw_extraction.get(
        "doc_id"
    )

    if not doc_id:
        raise ValueError(
            "raw_extraction is missing doc_id."
        )

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    mapped_rows: list[dict[str, Any]] = []
    dynamically_mapped_rows: list[dict[str, Any]] = []
    unmapped_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Process each extracted row
    # ------------------------------------------------------------------

    for row in rows:

        label = str(
            row.get("label", "")
        ).strip()

        if not label:
            continue

        statement = row.get(
            "sheet_type"
        )

        if not statement:

            skipped_rows.append(
                {
                    "sheet_name": row.get(
                        "sheet_name"
                    ),
                    "row_index": row.get(
                        "row_index"
                    ),
                    "label": label,
                    "reason": "missing_sheet_type",
                }
            )

            continue

        row_type = classify_row(
            row
        )

        # --------------------------------------------------------------
        # Notes
        #
        # Notes have a separate semantic structure and will be handled
        # by the Excel notes mapper.
        # --------------------------------------------------------------

        if statement == "notes":

            skipped_rows.append(
                {
                    "sheet_name": row.get(
                        "sheet_name"
                    ),
                    "row_index": row.get(
                        "row_index"
                    ),
                    "label": label,
                    "reason": "notes_handled_separately",
                }
            )

            continue

        # --------------------------------------------------------------
        # Ignore structural/control rows.
        # --------------------------------------------------------------

        if is_structural_row(
            label,
            row_type,
        ):

            skipped_rows.append(
                {
                    "sheet_name": row.get(
                        "sheet_name"
                    ),
                    "row_index": row.get(
                        "row_index"
                    ),
                    "label": label,
                    "reason": "structural_or_control_row",
                    "row_type": row_type,
                }
            )

            continue

        # --------------------------------------------------------------
        # First: explicit canonical mapping.
        # --------------------------------------------------------------

        target = map_label(
            label,
            statement,
        )

        dynamic = False

        # --------------------------------------------------------------
        # Second: conservative dynamic mapping.
        # --------------------------------------------------------------

        if target is None:

            target = build_dynamic_target(
                {
                    **row,
                    "row_type": row_type,
                }
            )

            dynamic = target is not None

        # --------------------------------------------------------------
        # No target.
        # --------------------------------------------------------------

        if target is None:

            unmapped_rows.append(
                {
                    "sheet_name": row.get(
                        "sheet_name"
                    ),
                    "row_index": row.get(
                        "row_index"
                    ),
                    "label": label,
                    "statement": statement,
                    "values": row.get(
                        "values",
                        {},
                    ),
                    "reason": "no_canonical_target",
                }
            )

            continue

        # --------------------------------------------------------------
        # Create ONLY this canonical target.
        # --------------------------------------------------------------

        try:

            node = create_target(
                canonical,
                target,
            )

        except TypeError as exc:

            unmapped_rows.append(
                {
                    "sheet_name": row.get(
                        "sheet_name"
                    ),
                    "row_index": row.get(
                        "row_index"
                    ),
                    "label": label,
                    "statement": statement,
                    "target": {
                        "statement": target.statement,
                        "path": list(
                            target.path
                        ),
                    },
                    "reason": "canonical_path_conflict",
                    "error": str(exc),
                }
            )

            continue

        # --------------------------------------------------------------
        # Add row type at account level.
        # --------------------------------------------------------------

        node["row_type"] = row_type

        values = row.get(
            "values",
            {},
        )

        cells = row.get(
            "cells",
            {},
        )

        sheet_name = row.get(
            "sheet_name",
            "",
        )

        written_periods: list[str] = []

        # --------------------------------------------------------------
        # Write actual values.
        # --------------------------------------------------------------

        for period in periods:

            value = values.get(
                period
            )

            # IMPORTANT:
            # None means unavailable.
            # Do not write it as zero.
            if value is None:
                continue

            cell = cells.get(
                period
            )

            if not cell:
                continue

            evidence = make_excel_evidence(
                doc_id=doc_id,
                sheet_name=sheet_name,
                cell=cell,
                row=label,
                period=period,
            )

            write_period_value(
                node,
                period=period,
                value=value,
                evidence=evidence,
            )

            written_periods.append(
                period
            )

        # --------------------------------------------------------------
        # If the mapped row has no actual values, remove the empty
        # canonical node again.
        #
        # This is important because a row with no values should not
        # create an empty canonical field.
        # --------------------------------------------------------------

        if not written_periods:

            remove_empty_target(
                canonical=canonical,
                target=target,
            )

            skipped_rows.append(
                {
                    "sheet_name": sheet_name,
                    "row_index": row.get(
                        "row_index"
                    ),
                    "label": label,
                    "reason": "row_has_no_values",
                }
            )

            continue

        mapping_record = {
            "sheet_name": sheet_name,
            "row_index": row.get(
                "row_index"
            ),
            "label": label,
            "statement": statement,
            "target": {
                "statement": target.statement,
                "path": list(
                    target.path
                ),
            },
            "periods": written_periods,
        }

        if dynamic:

            dynamically_mapped_rows.append(
                mapping_record
            )

        else:

            mapped_rows.append(
                mapping_record
            )

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    canonical["_excel_mapping_diagnostics"] = {
        "mapped_count": len(
            mapped_rows
        ),
        "dynamic_mapping_count": len(
            dynamically_mapped_rows
        ),
        "unmapped_count": len(
            unmapped_rows
        ),
        "skipped_count": len(
            skipped_rows
        ),
        "mapped_rows": mapped_rows,
        "dynamic_mapped_rows": dynamically_mapped_rows,
        "unmapped_rows": unmapped_rows,
        "skipped_rows": skipped_rows,
    }

    return canonical


# ---------------------------------------------------------------------------
# Remove empty target
# ---------------------------------------------------------------------------

def remove_empty_target(
    *,
    canonical: dict[str, Any],
    target: CanonicalTarget,
) -> None:
    """
    Remove a target that ended up with no actual period values.

    Also removes empty parent dictionaries created solely for that target.

    This keeps the final canonical JSON clean.
    """

    statements = canonical.get(
        "statements",
        {}
    )

    statement_node = statements.get(
        target.statement
    )

    if not isinstance(
        statement_node,
        dict,
    ):
        return

    current = statement_node
    parents: list[
        tuple[dict[str, Any], str]
    ] = []

    for part in target.path:

        if not isinstance(
            current,
            dict,
        ):
            return

        if part not in current:
            return

        parents.append(
            (
                current,
                part,
            )
        )

        current = current[part]

    # Remove target.
    parent, key = parents[-1]
    parent.pop(
        key,
        None,
    )

    # Remove empty parents bottom-up.
    for parent, key in reversed(
        parents[:-1]
    ):

        child = parent.get(
            key
        )

        if isinstance(
            child,
            dict,
        ) and not child:

            parent.pop(
                key,
                None,
            )

    # Remove empty statement.
    if not statement_node:
        statements.pop(
            target.statement,
            None,
        )


# ---------------------------------------------------------------------------
# Pipeline wrapper
# ---------------------------------------------------------------------------

def canonicalize_excel_pipeline(
    raw_extraction: dict[str, Any],
    structure: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    bank_id: str | None = None,
    bank_name: str | None = None,
    job_id: str | None = None,
) -> dict[str, Any]:

    return canonicalize_excel_rows(
        raw_extraction=raw_extraction,
        structure=structure,
        rows=rows,
        bank_id=bank_id,
        bank_name=bank_name,
        job_id=job_id,
    )


# ---------------------------------------------------------------------------
# Save helper
# ---------------------------------------------------------------------------

def save_canonical_json(
    canonical: dict[str, Any],
    output_path: str | Path,
) -> None:

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            canonical,
            file,
            indent=2,
            ensure_ascii=False,
        )
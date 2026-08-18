# Audit Lens --- Financial Statement Extraction Backend

## Overview

This repository contains the extraction layer for **Audit Lens**, an
AI-assisted Banking Financial Statement Review / Audit Copilot.

The current implementation focuses on reliably converting financial
statement documents into a **canonical financial-data structure** that
can be consumed by downstream deterministic review engines and
AI-assisted review components.

The extraction layer currently supports:

-   PDF financial statements
-   Excel (`.xlsx`) financial statements
-   Excel macro-enabled workbooks (`.xlsm`)
-   Sheet classification
-   Financial-period detection
-   Header/period-column detection
-   Row-level financial data extraction
-   Excel-to-canonical mapping
-   Evidence/provenance for extracted Excel values
-   A unified document extraction router

> **Important:** This is a copilot, not an autonomous auditor.
> Extraction and review results are intended for human review and final
> sign-off.

------------------------------------------------------------------------

## Current Architecture

The extraction flow is:

``` text
                    Input Document
                         |
                         v
                extraction_router.py
                    /          \
                   /            \
                 PDF            Excel
                  |                |
                  v                v
          pdf_extractor.py   excel_extractor.py
                  |                |
                  |          excel_structure.py
                  |                |
                  |          excel_columns.py
                  |                |
                  |          excel_rows.py
                  |                |
                  |      excel_canonical_mapper.py
                  |                |
                  +-------+--------+
                          |
                          v
                   Canonical JSON
```

The router provides one entry point regardless of whether the uploaded
document is a PDF or Excel workbook.

------------------------------------------------------------------------

## What Has Been Implemented

### 1. PDF Extraction

The existing PDF extraction pipeline is implemented in:

``` text
backend/extraction/pdf_extractor.py
```

It handles the existing PDF extraction and canonicalization flow.

The unified router calls the existing public PDF pipeline rather than
duplicating or rewriting its internal logic.

------------------------------------------------------------------------

### 2. Excel Raw Extraction

Implemented in:

``` text
backend/extraction/excel_extractor.py
```

This layer:

-   Opens `.xlsx` / `.xlsm` workbooks with `openpyxl`
-   Preserves worksheet names
-   Preserves row and cell references
-   Extracts raw cell values
-   Preserves source coordinates such as `C38`
-   Uses `data_only=True` so formula cells are read using their
    stored/calculated values when available

The extractor does **not** perform canonical mapping.

------------------------------------------------------------------------

### 3. Excel Sheet Classification and Structure Detection

Implemented in:

``` text
backend/extraction/excel_structure.py
```

This identifies worksheet types such as:

``` text
profit_and_loss
balance_sheet
cash_flow
notes
```

It also detects available financial periods.

For example:

``` text
FY2026
FY2025
```

------------------------------------------------------------------------

### 4. Excel Column / Header Detection

Implemented in:

``` text
backend/extraction/excel_columns.py
```

This determines:

-   Header row
-   Label column
-   Period columns

For example:

``` text
Balance Sheet
  Header row:   3
  Label column: A
  Periods:
    FY2026 -> C
    FY2025 -> D
```

This avoids hardcoding one fixed Excel layout for every workbook.

------------------------------------------------------------------------

### 5. Excel Row Extraction

Implemented in:

``` text
backend/extraction/excel_rows.py
```

This converts detected Excel rows into a normalized intermediate
representation containing information such as:

-   Sheet
-   Row number
-   Label
-   Period values
-   Source cell references

Example:

``` json
{
  "sheet_name": "Balance Sheet",
  "row_index": 8,
  "label": "Loans",
  "values": {
    "FY2026": 155000,
    "FY2025": 137000
  },
  "cells": {
    "FY2026": "C8",
    "FY2025": "D8"
  }
}
```

------------------------------------------------------------------------

### 6. Excel Canonical Mapper

Implemented in:

``` text
backend/extraction/excel_canonical_mapper.py
```

This maps the normalized Excel rows into the project's canonical
financial-data structure.

A key design decision is that the mapper **does not treat the example
canonical JSON as an absolute schema that must be populated
completely**.

If a financial item is absent or all of its values are unavailable, the
mapper can skip it instead of generating unnecessary null-only fields.

The mapper supports:

-   Explicit mappings
-   Dynamic mappings
-   Statement classification
-   Period-based values
-   Excel-specific evidence
-   Additional items where a suitable canonical field is not explicitly
    defined
-   Removal/skipping of empty targets

------------------------------------------------------------------------

## Canonical Data Structure

The downstream system consumes a normalized structure rather than raw
PDF/Excel-specific data.

For a typical line item, the structure follows the existing canonical
convention:

``` json
"cash_and_cash_equivalents": {
  "FY2025": {
    "value": 3200.0,
    "evidence": {
      "doc_id": "financial_statement.pdf",
      "page": 2,
      "table": "Balance Sheet",
      "row": "Cash and Cash Equivalents",
      "period": "FY2025"
    }
  },
  "FY2024": {
    "value": 2800.0,
    "evidence": {
      "doc_id": "financial_statement.pdf",
      "page": 2,
      "table": "Balance Sheet",
      "row": "Cash and Cash Equivalents",
      "period": "FY2024"
    }
  },
  "row_type": "line_item"
}
```

For Excel, the evidence is adapted to Excel's source model, including
worksheet and cell information where applicable.

The important principle is:

> **Values and evidence travel together through the extraction
> pipeline.**

This allows downstream findings to trace a financial value back to its
source.

------------------------------------------------------------------------

## Unified Extraction Router

Implemented in:

``` text
backend/extraction/extraction_router.py
```

The router detects the file extension and selects the appropriate
pipeline.

### Supported formats

``` text
.pdf
.xlsx
.xlsm
```

Conceptually:

``` python
if extension == ".pdf":
    use PDF pipeline

elif extension in {".xlsx", ".xlsm"}:
    use Excel pipeline

else:
    raise unsupported file type error
```

This means the rest of the application does not need to know which
extraction implementation is required.

------------------------------------------------------------------------

## Command-Line Entry Point

Implemented in:

``` text
backend/extraction/run_extr.py
```

It provides a simple way to test the unified extraction flow.

### Usage

From the project root:

``` powershell
python -m backend.extraction.run_extr "<document_path>"
```

An optional job ID can also be supplied:

``` powershell
python -m backend.extraction.run_extr "<document_path>" "<job_id>"
```

If no job ID is supplied during local testing, the default is:

``` text
local_test
```

------------------------------------------------------------------------

## Example: PDF

Example:

``` powershell
python -m backend.extraction.run_extr "backend\data\2 Horizon NBFC (PDF)\horizon_financial_services_dummy_dataset.pdf"
```

Expected result:

``` text
=== EXTRACTION SUCCESSFUL ===
Input:       ...
Source type: pdf
Job ID:      local_test
Output:      ..._canonical.json
```

------------------------------------------------------------------------

## Example: Excel

Example:

``` powershell
python -m backend.extraction.run_extr "backend\data\4 Meridian FInance NBFC (EXEL)\meridian_capital_finance_dummy_dataset_values_only.xlsx"
```

Expected result:

``` text
=== EXTRACTION SUCCESSFUL ===
Input:       ...
Source type: xlsx
Job ID:      local_test
Output:      ..._canonical.json
```

------------------------------------------------------------------------

## Project Structure

The relevant backend structure is currently:

``` text
backend/
├── data/
│   ├── 1 Sunrise Bank (EXEL)/
│   ├── 2 Horizon NBFC (PDF)/
│   ├── 4 Meridian FInance NBFC (EXEL)/
│   └── example.json
│
├── extraction/
│   ├── __init__.py
│   ├── excel_canonical_mapper.py
│   ├── excel_columns.py
│   ├── excel_extractor.py
│   ├── excel_rows.py
│   ├── excel_structure.py
│   ├── extraction_router.py
│   ├── mappings.py
│   ├── pdf_extractor.py
│   └── run_extr.py
│
└── requirements.txt
```

Local development/testing folders are intentionally excluded from Git
through `.gitignore`.

Generated extraction outputs such as:

``` text
*_canonical.json
*_raw_extraction.json
```

are also excluded from Git.

------------------------------------------------------------------------

## Installation

Create/activate the project virtual environment and install the backend
requirements:

``` powershell
pip install -r backend\requirements.txt
```

If using the existing project environment:

``` powershell
(finenv) PS D:\Cognizant NPN\Financial Review System>
```

run the commands from the project root.

------------------------------------------------------------------------

## Testing the Extraction Layer

At minimum, test both supported document types.

### PDF test

``` powershell
python -m backend.extraction.run_extr "backend\data\2 Horizon NBFC (PDF)\horizon_financial_services_dummy_dataset.pdf"
```

### Excel test

``` powershell
python -m backend.extraction.run_extr "backend\data\4 Meridian FInance NBFC (EXEL)\meridian_capital_finance_dummy_dataset_values_only.xlsx"
```

Both should produce a canonical JSON output.

------------------------------------------------------------------------

## Excel Formula Handling

The Excel extraction currently uses:

``` python
load_workbook(
    filename=file_path,
    data_only=True,
)
```

This is intentional for the MVP.

The test workbook was converted to a values-only dataset so that the
extraction pipeline receives financial values directly rather than
relying on formula expressions.

For example:

``` text
C38 = 55040
D38 = 50800
```

instead of:

``` text
C38 = =SUM(C36:C37)
D38 = =SUM(D36:D37)
```

The extraction layer therefore focuses on the resulting financial
values.

> Deterministic calculations and review checks should still be performed
> by Python/code in downstream review engines, not by an LLM.

------------------------------------------------------------------------

## Evidence / Provenance

Evidence is a core part of the extraction design.

For PDF values, evidence can contain information such as:

``` text
doc_id
page
table
row
period
```

For Excel values, evidence can use Excel-specific information such as:

``` text
doc_id
sheet
cell
row
period
```

The purpose is to allow a reviewer to follow:

``` text
Finding
   ↓
Canonical value
   ↓
Evidence
   ↓
Original document
```

This will later support the project's intended review workflow:

``` text
Finding → Evidence → Explanation → WP-514
```

------------------------------------------------------------------------

## Current Scope

The extraction layer currently provides:

-   PDF extraction
-   Excel extraction
-   PDF canonicalization
-   Excel canonicalization
-   Period detection
-   Sheet classification
-   Excel column detection
-   Row normalization
-   Evidence propagation
-   Unified document routing
-   Local command-line execution

------------------------------------------------------------------------

## Next Layer

The extraction layer is intended to feed the deterministic financial
review engines.

The broader target architecture is:

``` text
Upload
   ↓
API / Orchestrator
   ↓
Document Extraction
   ↓
Canonical Financial Data
   ↓
Evidence Mapping
   ↓
 ┌───────────────────────┐
 │                       │
 ▼                       ▼
Math Engine        Consistency / PY Engine
 │                       │
 └───────────┬───────────┘
             ↓
         AI Review
             ↓
      Findings Aggregator
             ↓
           WP-514
             ↓
         Dashboard
```

The next major implementation area is the **deterministic review/math
engine**, including checks such as:

-   Total Assets = Total Liabilities + Total Equity
-   Total Income - Total Expenses = Net Profit/Loss
-   Opening Cash + Net Cash Flow = Closing Cash
-   Equity roll-forward
-   Subtotal/footing checks
-   Prior-year movements
-   Cross-statement consistency checks

These calculations should be performed using deterministic Python logic.

------------------------------------------------------------------------

## Design Principles

### Deterministic numbers

Financial arithmetic and deterministic review checks must not be
delegated to an LLM.

### Grounded AI

AI should receive validated financial data, deterministic findings, and
relevant evidence. It should explain and summarize rather than invent or
alter financial values.

### Evidence first

Extracted values should retain their source information so that findings
remain traceable.

### Missing data is not zero

Missing information should remain missing rather than being silently
converted into `0`.

### Human review remains mandatory

The system is an **audit/review copilot**. It does not replace
professional judgement or reviewer sign-off.

------------------------------------------------------------------------

## Git Workflow

The extraction implementation is currently developed on:

``` text
feature/extraction
```

The branch is intended to be reviewed before merging into the shared
`main` branch.

Typical workflow:

``` powershell
git status
git add <files>
git commit -m "Describe change"
git push
```

Avoid force-pushing to shared branches.

------------------------------------------------------------------------

## Troubleshooting

### Document not found

If you see:

``` text
Error: Document not found: ...
```

verify the path:

``` powershell
Get-ChildItem -Path . -Filter "<filename>" -Recurse
```

Then run the extractor using the exact returned path.

### Unsupported file type

The router currently supports:

``` text
.pdf
.xlsx
.xlsm
```

Other extensions will return an unsupported-file-type error.

### Extraction failure

The command-line runner reports the exception rather than silently
failing:

``` text
=== EXTRACTION FAILED ===
File: ...
Error: ...
```

This is intentional so extraction failures remain visible during
development.

------------------------------------------------------------------------

## Status

### Extraction Layer

  Component                   Status
  --------------------------- -------------
  PDF extraction              Implemented
  Excel raw extraction        Implemented
  Excel structure detection   Implemented
  Excel column detection      Implemented
  Excel row extraction        Implemented
  Excel canonical mapper      Implemented
  Evidence mapping            Implemented
  Unified extraction router   Implemented
  CLI extraction runner       Implemented
  GitHub feature branch       Created

The current branch provides a working foundation for the next stage of
the Audit Lens financial review pipeline.

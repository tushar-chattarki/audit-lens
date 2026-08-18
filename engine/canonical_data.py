def get_value(data, path, period="FY2025"):
    """
    Safely retrieve a financial value.

    Supports:
    1. Final canonical financial JSON
       - FY2025 / FY2024 structure
    2. Existing mock financial JSON
       - current_year / prior_year structure
    """
    if period is None:
        period = "FY2025"

    # ========================================================
    # FINAL JSON STRUCTURE
    # ========================================================
    current = data

    try:
        for key in path:
            current = current[key]

        period_data = current.get(period)

        if period_data and isinstance(period_data, dict):
            return period_data.get("value")

    except (KeyError, TypeError, AttributeError):
        pass

    # ========================================================
    # MOCK JSON FALLBACK
    # ========================================================
    mock_mapping = {
        "FY2025": "current_year",
        "FY2024": "prior_year",
        "current_year": "current_year",
        "prior_year": "prior_year"
    }

    mock_period = mock_mapping.get(period, "current_year")
    root = data if mock_period == "current_year" else data.get("prior_year_data", {})

    if not isinstance(root, dict):
        return None

    try:
        last_key = path[-1]

        # Balance Sheet items
        if last_key == "cash_and_cash_equivalents":
            return root.get("balance_sheet", {}).get("cash")

        if last_key == "total_assets":
            return root.get("balance_sheet", {}).get("total_assets")

        if last_key == "total_liabilities":
            return root.get("balance_sheet", {}).get("total_liabilities")

        if last_key == "total_equity":
            return root.get("balance_sheet", {}).get("total_equity")

        if last_key == "opening_equity":
            return root.get("balance_sheet", {}).get("opening_equity")

        if last_key == "closing_equity":
            return root.get("balance_sheet", {}).get("total_equity")

        # Profit and Loss items
        if last_key in ("v_profit_for_the_year", "net_income"):
            return root.get("income_statement", {}).get("net_income")

        if last_key in ("depreciation_and_amortisation", "depreciation"):
            if "notes" in path:
                return root.get("notes", {}).get("depreciation")
            return root.get("income_statement", {}).get("depreciation")

        if last_key == "tax_expense":
            if "notes" in path:
                return root.get("notes", {}).get("tax_expense")
            return root.get("income_statement", {}).get("tax_expense")

        if last_key in ("dividends_paid", "dividends"):
            if "notes" in path:
                return root.get("notes", {}).get("dividends")
            return root.get("income_statement", {}).get("dividends")

        # Cash Flow items
        if last_key in ("closing_cash", "ending_cash"):
            return root.get("cash_flow", {}).get("ending_cash")

        if last_key in ("opening_cash", "beginning_cash"):
            return root.get("cash_flow", {}).get("beginning_cash")

        # Notes items
        if last_key in ("note_12_cash", "cash"):
            if "notes" in path:
                return root.get("notes", {}).get("cash")

        if last_key in ("note_depreciation", "notes_depreciation"):
            return root.get("notes", {}).get("depreciation")

        if last_key in ("note_tax_expense", "notes_tax_expense"):
            return root.get("notes", {}).get("tax_expense")

        if last_key in ("note_dividends", "notes_dividends"):
            return root.get("notes", {}).get("dividends")

    except (KeyError, TypeError, AttributeError):
        return None

    return None


def get_evidence(data, path, period="FY2025"):
    """
    Safely retrieve evidence for a financial value.
    """
    if period is None:
        period = "FY2025"

    current = data

    try:
        for key in path:
            current = current[key]

        period_data = current.get(period)

        if not period_data or not isinstance(period_data, dict):
            return []

        evidence = period_data.get("evidence")

        if evidence:
            return [evidence]

        return []

    except (KeyError, TypeError, AttributeError):
        return []


# ============================================================
# BALANCE SHEET
# ============================================================

def get_cash(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "balance_sheet",
            "assets",
            "cash_and_cash_equivalents"
        ],
        period
    )


def get_total_assets(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "balance_sheet",
            "assets",
            "total_assets"
        ],
        period
    )


def get_total_liabilities(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "balance_sheet",
            "liabilities",
            "total_liabilities"
        ],
        period
    )


def get_total_equity(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "balance_sheet",
            "equity",
            "total_equity"
        ],
        period
    )


# ============================================================
# PROFIT & LOSS
# ============================================================

def get_net_income(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "profit_and_loss",
            "v_profit_for_the_year"
        ],
        period
    )


def get_depreciation(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "profit_and_loss",
            "depreciation_and_amortisation"
        ],
        period
    )


def get_tax_expense(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "profit_and_loss",
            "profit",
            "tax_expense"
        ],
        period
    )


# ============================================================
# CASH FLOW
# ============================================================

def get_opening_cash(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "cash_flow",
            "opening_cash"
        ],
        period
    )


def get_closing_cash(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "cash_flow",
            "closing_cash"
        ],
        period
    )


# ============================================================
# NOTES
# ============================================================

def get_notes_cash(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "notes",
            "note_12_cash"
        ],
        period
    )


def get_notes_depreciation(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "notes",
            "depreciation"
        ],
        period
    )


def get_notes_tax_expense(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "notes",
            "tax_expense"
        ],
        period
    )


def get_notes_dividends(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "notes",
            "dividends"
        ],
        period
    )


# ============================================================
# EQUITY
# ============================================================

def get_opening_equity(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "equity",
            "opening_equity"
        ],
        period
    )


def get_dividends(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "equity",
            "dividends_paid"
        ],
        period
    )


def get_closing_equity(data, period="FY2025"):
    return get_value(
        data,
        [
            "statements",
            "equity",
            "closing_equity"
        ],
        period
    )
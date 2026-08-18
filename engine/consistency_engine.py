from engine.findings import create_finding
from engine.canonical_data import (
    get_cash,
    get_closing_cash,
    get_notes_cash,
    get_depreciation,
    get_notes_depreciation,
    get_tax_expense,
    get_notes_tax_expense,
    get_dividends,
    get_notes_dividends,
    get_opening_equity,
    get_total_equity,
    get_net_income
)


# ============================================================
# C001 - Cash consistency across BS, CF, and Notes
# ============================================================

def check_cash_consistency(data):
    bs_cash = get_cash(data)
    cf_cash = get_closing_cash(data)
    note_cash = get_notes_cash(data)

    if bs_cash is None or cf_cash is None or note_cash is None:
        return create_finding(
            rule_id="C001",
            category="consistency",
            status="REVIEW",
            severity="Medium",
            message="Cash balances cannot be verified across all statements because some disclosures are unavailable.",
            values={
                "balance_sheet": bs_cash,
                "cash_flow": cf_cash,
                "notes": note_cash
            },
            evidence=[]
        )

    if bs_cash == cf_cash == note_cash:
        return create_finding(
            rule_id="C001",
            category="consistency",
            status="PASS",
            severity="None",
            message="Cash balances are consistent across the Balance Sheet, Cash Flow Statement and Notes.",
            values={
                "balance_sheet": bs_cash,
                "cash_flow": cf_cash,
                "notes": note_cash
            },
            evidence=[]
        )

    return create_finding(
        rule_id="C001",
        category="consistency",
        status="FAIL",
        severity="High",
        message="Cash balance is inconsistent across financial statements and notes.",
        values={
            "balance_sheet": bs_cash,
            "cash_flow": cf_cash,
            "notes": note_cash
        },
        evidence=[
            {
                "source": "Balance Sheet",
                "field": "Cash",
                "value": bs_cash
            },
            {
                "source": "Cash Flow Statement",
                "field": "Ending Cash",
                "value": cf_cash
            },
            {
                "source": "Notes",
                "field": "Cash",
                "value": note_cash
            }
        ]
    )


# ============================================================
# C002 - Cash Flow vs Notes
# ============================================================

def check_cash_flow_vs_notes(data):
    cf_cash = get_closing_cash(data)
    note_cash = get_notes_cash(data)

    if cf_cash is None or note_cash is None:
        return create_finding(
            rule_id="C002",
            category="consistency",
            status="REVIEW",
            severity="Medium",
            message="Cash Flow ending cash or Notes cash disclosure is unavailable.",
            values={
                "cash_flow": cf_cash,
                "notes": note_cash
            },
            evidence=[]
        )

    if cf_cash == note_cash:
        return create_finding(
            rule_id="C002",
            category="consistency",
            status="PASS",
            severity="None",
            message="Cash Flow ending cash agrees with the cash disclosed in the Notes.",
            values={
                "cash_flow": cf_cash,
                "notes": note_cash
            },
            evidence=[]
        )

    difference = cf_cash - note_cash
    return create_finding(
        rule_id="C002",
        category="consistency",
        status="FAIL",
        severity="High",
        message="Cash Flow ending cash does not agree with the cash disclosed in the Notes.",
        values={
            "cash_flow": cf_cash,
            "notes": note_cash,
            "difference": difference
        },
        evidence=[
            {
                "source": "Cash Flow Statement",
                "field": "Ending Cash",
                "value": cf_cash
            },
            {
                "source": "Notes",
                "field": "Cash",
                "value": note_cash
            }
        ]
    )


# ============================================================
# C003 - Balance Sheet vs Notes
# ============================================================

def check_balance_sheet_vs_notes(data):
    bs_cash = get_cash(data)
    note_cash = get_notes_cash(data)

    if bs_cash is None or note_cash is None:
        return create_finding(
            rule_id="C003",
            category="consistency",
            status="REVIEW",
            severity="Medium",
            message="Balance Sheet cash or Notes cash disclosure is unavailable.",
            values={
                "balance_sheet": bs_cash,
                "notes": note_cash
            },
            evidence=[]
        )

    if bs_cash == note_cash:
        return create_finding(
            rule_id="C003",
            category="consistency",
            status="PASS",
            severity="None",
            message="Balance Sheet cash agrees with the cash disclosed in the Notes.",
            values={
                "balance_sheet": bs_cash,
                "notes": note_cash
            },
            evidence=[]
        )

    difference = bs_cash - note_cash
    return create_finding(
        rule_id="C003",
        category="consistency",
        status="FAIL",
        severity="High",
        message="Balance Sheet cash does not agree with the cash disclosed in the Notes.",
        values={
            "balance_sheet": bs_cash,
            "notes": note_cash,
            "difference": difference
        },
        evidence=[
            {
                "source": "Balance Sheet",
                "field": "Cash",
                "value": bs_cash
            },
            {
                "source": "Notes",
                "field": "Cash",
                "value": note_cash
            }
        ]
    )


# ============================================================
# C004 - Equity roll-forward
# ============================================================

def check_equity_rollforward(data):
    opening_equity = get_opening_equity(data)
    net_income = get_net_income(data)
    dividends = get_dividends(data)
    actual_equity = get_total_equity(data)

    if (
        opening_equity is None
        or net_income is None
        or dividends is None
        or actual_equity is None
    ):
        return create_finding(
            rule_id="C004",
            category="consistency",
            status="REVIEW",
            severity="Medium",
            message="Equity roll-forward cannot be calculated because one or more components are unavailable.",
            values={
                "opening_equity": opening_equity,
                "net_income": net_income,
                "dividends": dividends,
                "actual_equity": actual_equity
            },
            evidence=[]
        )

    expected_equity = opening_equity + net_income - dividends
    difference = actual_equity - expected_equity

    if actual_equity == expected_equity:
        return create_finding(
            rule_id="C004",
            category="consistency",
            status="PASS",
            severity="None",
            message="Equity roll-forward is consistent.",
            values={
                "opening_equity": opening_equity,
                "net_income": net_income,
                "dividends": dividends,
                "expected_equity": expected_equity,
                "actual_equity": actual_equity,
                "difference": difference
            },
            evidence=[]
        )

    return create_finding(
        rule_id="C004",
        category="consistency",
        status="FAIL",
        severity="High",
        message="Equity roll-forward is inconsistent.",
        values={
            "opening_equity": opening_equity,
            "net_income": net_income,
            "dividends": dividends,
            "expected_equity": expected_equity,
            "actual_equity": actual_equity,
            "difference": difference
        },
        evidence=[
            {
                "source": "Balance Sheet",
                "field": "Opening Equity",
                "value": opening_equity
            },
            {
                "source": "Income Statement",
                "field": "Net Income",
                "value": net_income
            },
            {
                "source": "Income Statement",
                "field": "Dividends",
                "value": dividends
            },
            {
                "source": "Balance Sheet",
                "field": "Total Equity",
                "value": actual_equity
            }
        ]
    )


# ============================================================
# C005 - Depreciation vs Notes
# ============================================================

def check_depreciation_vs_notes(data):
    depreciation = get_depreciation(data)
    note_depreciation = get_notes_depreciation(data)

    if depreciation is None or note_depreciation is None:
        return create_finding(
            rule_id="C005",
            category="consistency",
            status="REVIEW",
            severity="Medium",
            message="Depreciation disclosure or Income Statement value is unavailable.",
            values={
                "income_statement": depreciation,
                "notes": note_depreciation
            },
            evidence=[]
        )

    if depreciation == note_depreciation:
        return create_finding(
            rule_id="C005",
            category="consistency",
            status="PASS",
            severity="None",
            message="Depreciation agrees with the amount disclosed in the Notes.",
            values={
                "income_statement": depreciation,
                "notes": note_depreciation
            },
            evidence=[]
        )

    difference = depreciation - note_depreciation
    return create_finding(
        rule_id="C005",
        category="consistency",
        status="FAIL",
        severity="High",
        message="Depreciation does not agree with the amount disclosed in the Notes.",
        values={
            "income_statement": depreciation,
            "notes": note_depreciation,
            "difference": difference
        },
        evidence=[
            {
                "source": "Income Statement",
                "field": "Depreciation",
                "value": depreciation
            },
            {
                "source": "Notes",
                "field": "Depreciation",
                "value": note_depreciation
            }
        ]
    )


# ============================================================
# C006 - Tax vs Notes
# ============================================================

def check_tax_vs_notes(data):
    tax_expense = get_tax_expense(data)
    note_tax = get_notes_tax_expense(data)

    if tax_expense is None or note_tax is None:
        return create_finding(
            rule_id="C006",
            category="consistency",
            status="REVIEW",
            severity="Medium",
            message="Tax expense disclosure or Income Statement value is unavailable.",
            values={
                "income_statement": tax_expense,
                "notes": note_tax
            },
            evidence=[]
        )

    if tax_expense == note_tax:
        return create_finding(
            rule_id="C006",
            category="consistency",
            status="PASS",
            severity="None",
            message="Tax expense agrees with the amount disclosed in the Notes.",
            values={
                "income_statement": tax_expense,
                "notes": note_tax
            },
            evidence=[]
        )

    difference = tax_expense - note_tax
    return create_finding(
        rule_id="C006",
        category="consistency",
        status="FAIL",
        severity="High",
        message="Tax expense does not agree with the amount disclosed in the Notes.",
        values={
            "income_statement": tax_expense,
            "notes": note_tax,
            "difference": difference
        },
        evidence=[
            {
                "source": "Income Statement",
                "field": "Tax Expense",
                "value": tax_expense
            },
            {
                "source": "Notes",
                "field": "Tax Expense",
                "value": note_tax
            }
        ]
    )


# ============================================================
# C007 - Dividends vs Notes
# ============================================================

def check_dividends_vs_notes(data):
    dividends = get_dividends(data)
    note_dividends = get_notes_dividends(data)

    if dividends is None or note_dividends is None:
        return create_finding(
            rule_id="C007",
            category="consistency",
            status="REVIEW",
            severity="Medium",
            message="Dividends disclosure or statement value is unavailable.",
            values={
                "income_statement": dividends,
                "notes": note_dividends
            },
            evidence=[]
        )

    if dividends == note_dividends:
        return create_finding(
            rule_id="C007",
            category="consistency",
            status="PASS",
            severity="None",
            message="Dividends agree with the amount disclosed in the Notes.",
            values={
                "income_statement": dividends,
                "notes": note_dividends
            },
            evidence=[]
        )

    difference = dividends - note_dividends
    return create_finding(
        rule_id="C007",
        category="consistency",
        status="FAIL",
        severity="High",
        message="Dividends do not agree with the amount disclosed in the Notes.",
        values={
            "income_statement": dividends,
            "notes": note_dividends,
            "difference": difference
        },
        evidence=[
            {
                "source": "Income Statement",
                "field": "Dividends",
                "value": dividends
            },
            {
                "source": "Notes",
                "field": "Dividends",
                "value": note_dividends
            }
        ]
    )
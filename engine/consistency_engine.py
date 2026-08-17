from engine.findings import create_finding


# C001
def check_cash_consistency(data):

    bs_cash = data["balance_sheet"]["cash"]
    cf_cash = data["cash_flow"]["ending_cash"]
    note_cash = data["notes"]["cash"]

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

    else:

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


# C002
def check_cash_flow_vs_notes(data):

    cf_cash = data["cash_flow"]["ending_cash"]
    note_cash = data["notes"]["cash"]

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


# C003
def check_balance_sheet_vs_notes(data):

    bs_cash = data["balance_sheet"]["cash"]
    note_cash = data["notes"]["cash"]

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


# C005
def check_depreciation_vs_notes(data):

    depreciation = data["income_statement"]["depreciation"]
    note_depreciation = data["notes"]["depreciation"]

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

# C006
def check_tax_vs_notes(data):

    tax_expense = data["income_statement"]["tax_expense"]
    note_tax = data["notes"]["tax_expense"]

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

# C007
def check_dividends_vs_notes(data):

    dividends = data["income_statement"]["dividends"]
    note_dividends = data["notes"]["dividends"]

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

# C004
def check_equity_rollforward(data):

    opening_equity = data["balance_sheet"]["opening_equity"]
    net_income = data["income_statement"]["net_income"]
    dividends = data["income_statement"]["dividends"]
    actual_equity = data["balance_sheet"]["total_equity"]

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
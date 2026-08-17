from engine.findings import create_finding

def calculate_movement(current_value, prior_value):
    """
    Calculate the absolute difference and percentage movement
    between current-year and prior-year values.
    """

    difference = current_value - prior_value

    if prior_value == 0:
        return difference, None

    movement_percentage = (
        difference / abs(prior_value)
    ) * 100

    return difference, movement_percentage
# MVP threshold for unusual prior-year movements.
# This is configurable and is an implementation choice,
# not a threshold specified in the project PDF.
UNUSUAL_MOVEMENT_THRESHOLD = 20.0

#PY001
def check_cash_prior_year(data):

    current_cash = data["balance_sheet"]["cash"]
    prior_cash = data["prior_year_data"]["balance_sheet"]["cash"]

    difference, movement_percentage = calculate_movement(
    current_cash,
    prior_cash
)
    if movement_percentage is None:
        status = "REVIEW"
        severity = "Medium"
        message = (
            "Prior-year cash is zero, so percentage movement "
            "cannot be calculated."
        )

    elif abs(movement_percentage) > UNUSUAL_MOVEMENT_THRESHOLD:
        status = "UNUSUAL"
        severity = "Medium"
        message = (
            "Cash shows an unusual movement compared with the prior year."
        )

    else:
        status = "PASS"
        severity = "None"
        message = (
            "Cash movement compared with the prior year "
            "is within the configured threshold."
        )

    return create_finding(
        rule_id="PY001",
        category="prior_year",
        status=status,
        severity=severity,
        message=message,
        values={
            "account": "Cash",
            "current_year": current_cash,
            "prior_year": prior_cash,
            "difference": difference,
            "movement_percentage": movement_percentage
        },
        evidence=[
            {
                "source": "Current Year Balance Sheet",
                "field": "Cash",
                "value": current_cash
            },
            {
                "source": "Prior Year Balance Sheet",
                "field": "Cash",
                "value": prior_cash
            }
        ]
    )
#PY002
def check_assets_prior_year(data):

    current_assets = data["balance_sheet"]["total_assets"]
    prior_assets = data["prior_year_data"]["balance_sheet"]["total_assets"]

    difference, movement_percentage = calculate_movement(
        current_assets,
        prior_assets
    )

    if movement_percentage is None:
        status = "REVIEW"
        severity = "Medium"
        message = (
            "Prior-year total assets are zero, so percentage movement "
            "cannot be calculated."
        )

    elif abs(movement_percentage) > UNUSUAL_MOVEMENT_THRESHOLD:
        status = "UNUSUAL"
        severity = "Medium"
        message = (
            "Total assets show an unusual movement compared "
            "with the prior year."
        )

    else:
        status = "PASS"
        severity = "None"
        message = (
            "Total asset movement compared with the prior year "
            "is within the configured threshold."
        )

    return create_finding(
        rule_id="PY002",
        category="prior_year",
        status=status,
        severity=severity,
        message=message,
        values={
            "account": "Total Assets",
            "current_year": current_assets,
            "prior_year": prior_assets,
            "difference": difference,
            "movement_percentage": movement_percentage
        },
        evidence=[
            {
                "source": "Current Year Balance Sheet",
                "field": "Total Assets",
                "value": current_assets
            },
            {
                "source": "Prior Year Balance Sheet",
                "field": "Total Assets",
                "value": prior_assets
            }
        ]
    )


#PY003
def check_liabilities_prior_year(data):

    current_liabilities = data["balance_sheet"]["total_liabilities"]
    prior_liabilities = (
        data["prior_year_data"]["balance_sheet"]["total_liabilities"]
    )

    difference, movement_percentage = calculate_movement(
        current_liabilities,
        prior_liabilities
    )

    if movement_percentage is None:
        status = "REVIEW"
        severity = "Medium"
        message = (
            "Prior-year total liabilities are zero, so percentage movement "
            "cannot be calculated."
        )

    elif abs(movement_percentage) > UNUSUAL_MOVEMENT_THRESHOLD:
        status = "UNUSUAL"
        severity = "Medium"
        message = (
            "Total liabilities show an unusual movement compared "
            "with the prior year."
        )

    else:
        status = "PASS"
        severity = "None"
        message = (
            "Total liability movement compared with the prior year "
            "is within the configured threshold."
        )

    return create_finding(
        rule_id="PY003",
        category="prior_year",
        status=status,
        severity=severity,
        message=message,
        values={
            "account": "Total Liabilities",
            "current_year": current_liabilities,
            "prior_year": prior_liabilities,
            "difference": difference,
            "movement_percentage": movement_percentage
        },
        evidence=[
            {
                "source": "Current Year Balance Sheet",
                "field": "Total Liabilities",
                "value": current_liabilities
            },
            {
                "source": "Prior Year Balance Sheet",
                "field": "Total Liabilities",
                "value": prior_liabilities
            }
        ]
    )

#PY004
def check_equity_prior_year(data):

    current_equity = data["balance_sheet"]["total_equity"]
    prior_equity = data["prior_year_data"]["balance_sheet"]["total_equity"]

    difference, movement_percentage = calculate_movement(
        current_equity,
        prior_equity
    )

    if movement_percentage is None:
        status = "REVIEW"
        severity = "Medium"
        message = (
            "Prior-year total equity is zero, so percentage movement "
            "cannot be calculated."
        )

    elif abs(movement_percentage) > UNUSUAL_MOVEMENT_THRESHOLD:
        status = "UNUSUAL"
        severity = "Medium"
        message = (
            "Total equity shows an unusual movement compared "
            "with the prior year."
        )

    else:
        status = "PASS"
        severity = "None"
        message = (
            "Total equity movement compared with the prior year "
            "is within the configured threshold."
        )

    return create_finding(
        rule_id="PY004",
        category="prior_year",
        status=status,
        severity=severity,
        message=message,
        values={
            "account": "Total Equity",
            "current_year": current_equity,
            "prior_year": prior_equity,
            "difference": difference,
            "movement_percentage": movement_percentage
        },
        evidence=[
            {
                "source": "Current Year Balance Sheet",
                "field": "Total Equity",
                "value": current_equity
            },
            {
                "source": "Prior Year Balance Sheet",
                "field": "Total Equity",
                "value": prior_equity
            }
        ]
    )

#PY005
def check_net_income_prior_year(data):

    current_income = data["income_statement"]["net_income"]
    prior_income = data["prior_year_data"]["income_statement"]["net_income"]

    difference, movement_percentage = calculate_movement(
        current_income,
        prior_income
    )

    if movement_percentage is None:
        status = "REVIEW"
        severity = "Medium"
        message = "Prior-year net income is zero, so percentage movement cannot be calculated."

    elif abs(movement_percentage) > UNUSUAL_MOVEMENT_THRESHOLD:
        status = "UNUSUAL"
        severity = "Medium"
        message = "Net income shows an unusual movement compared with the prior year."

    else:
        status = "PASS"
        severity = "None"
        message = "Net income movement is within the configured threshold."

    return create_finding(
        rule_id="PY005",
        category="prior_year",
        status=status,
        severity=severity,
        message=message,
        values={
            "account": "Net Income",
            "current_year": current_income,
            "prior_year": prior_income,
            "difference": difference,
            "movement_percentage": movement_percentage
        },
        evidence=[
            {
                "source": "Current Year Income Statement",
                "field": "Net Income",
                "value": current_income
            },
            {
                "source": "Prior Year Income Statement",
                "field": "Net Income",
                "value": prior_income
            }
        ]
    )

#PY006
def check_depreciation_prior_year(data):

    current_dep = data["income_statement"]["depreciation"]
    prior_dep = data["prior_year_data"]["income_statement"]["depreciation"]

    difference, movement_percentage = calculate_movement(
        current_dep,
        prior_dep
    )

    if movement_percentage is None:
        status = "REVIEW"
        severity = "Medium"
        message = "Prior-year depreciation is zero, so percentage movement cannot be calculated."

    elif abs(movement_percentage) > UNUSUAL_MOVEMENT_THRESHOLD:
        status = "UNUSUAL"
        severity = "Medium"
        message = "Depreciation shows an unusual movement compared with the prior year."

    else:
        status = "PASS"
        severity = "None"
        message = "Depreciation movement is within the configured threshold."

    return create_finding(
        rule_id="PY006",
        category="prior_year",
        status=status,
        severity=severity,
        message=message,
        values={
            "account": "Depreciation",
            "current_year": current_dep,
            "prior_year": prior_dep,
            "difference": difference,
            "movement_percentage": movement_percentage
        },
        evidence=[
            {
                "source": "Current Year Income Statement",
                "field": "Depreciation",
                "value": current_dep
            },
            {
                "source": "Prior Year Income Statement",
                "field": "Depreciation",
                "value": prior_dep
            }
        ]
    )

#PY007
def check_tax_prior_year(data):

    current_tax = data["income_statement"]["tax_expense"]
    prior_tax = data["prior_year_data"]["income_statement"]["tax_expense"]

    difference, movement_percentage = calculate_movement(
        current_tax,
        prior_tax
    )

    if movement_percentage is None:
        status = "REVIEW"
        severity = "Medium"
        message = "Prior-year tax expense is zero, so percentage movement cannot be calculated."

    elif abs(movement_percentage) > UNUSUAL_MOVEMENT_THRESHOLD:
        status = "UNUSUAL"
        severity = "Medium"
        message = "Tax expense shows an unusual movement compared with the prior year."

    else:
        status = "PASS"
        severity = "None"
        message = "Tax expense movement is within the configured threshold."

    return create_finding(
        rule_id="PY007",
        category="prior_year",
        status=status,
        severity=severity,
        message=message,
        values={
            "account": "Tax Expense",
            "current_year": current_tax,
            "prior_year": prior_tax,
            "difference": difference,
            "movement_percentage": movement_percentage
        },
        evidence=[
            {
                "source": "Current Year Income Statement",
                "field": "Tax Expense",
                "value": current_tax
            },
            {
                "source": "Prior Year Income Statement",
                "field": "Tax Expense",
                "value": prior_tax
            }
        ]
    )

#PY008
def check_dividends_prior_year(data):

    current_div = data["income_statement"]["dividends"]
    prior_div = data["prior_year_data"]["income_statement"]["dividends"]

    difference, movement_percentage = calculate_movement(
        current_div,
        prior_div
    )

    if movement_percentage is None:
        status = "REVIEW"
        severity = "Medium"
        message = "Prior-year dividends are zero, so percentage movement cannot be calculated."

    elif abs(movement_percentage) > UNUSUAL_MOVEMENT_THRESHOLD:
        status = "UNUSUAL"
        severity = "Medium"
        message = "Dividends show an unusual movement compared with the prior year."

    else:
        status = "PASS"
        severity = "None"
        message = "Dividend movement is within the configured threshold."

    return create_finding(
        rule_id="PY008",
        category="prior_year",
        status=status,
        severity=severity,
        message=message,
        values={
            "account": "Dividends",
            "current_year": current_div,
            "prior_year": prior_div,
            "difference": difference,
            "movement_percentage": movement_percentage
        },
        evidence=[
            {
                "source": "Current Year Income Statement",
                "field": "Dividends",
                "value": current_div
            },
            {
                "source": "Prior Year Income Statement",
                "field": "Dividends",
                "value": prior_div
            }
        ]
    )
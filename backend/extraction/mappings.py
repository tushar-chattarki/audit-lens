from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CanonicalTarget:
    statement: str
    path: tuple[str, ...]


# ---------------------------------------------------------------------------
# Section / heading labels
# ---------------------------------------------------------------------------

PARENT_LABELS = {
    # Balance Sheet
    "capital and liabilities",
    "assets",
    "liabilities",
    "equity",
    "shareholders equity",
    "shareholders funds",

    # Profit & Loss
    "i income",
    "income",
    "ii expenditure",
    "expenditure",
    "expenses",
    "iii profit loss",
    "profit loss",
    "profit and loss",
    "profit",

    # Cash Flow
    "a cash flow from operating activities",
    "b cash flow from investing activities",
    "c cash flow from financing activities",
    "cash flow from operating activities",
    "cash flow from investing activities",
    "cash flow from financing activities",

    # Generic
    "particulars",
}


# ---------------------------------------------------------------------------
# Label normalization
# ---------------------------------------------------------------------------

ENUMERATION_PREFIX_PATTERN = re.compile(
    r"^(?:i|ii|iii|iv|v|vi|vii|viii|a|b|c|d|e)\b[\.\s]*"
)

def normalize_label(label: str) -> str:
    normalized = str(label).lower().strip()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"\([^)]*\)", " ", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.strip()

    # Strip leading enumeration markers ("I.", "II.", "A.") that show up on
    # Indian-format statements but carry no semantic meaning for matching.
    normalized = ENUMERATION_PREFIX_PATTERN.sub("", normalized).strip()

    return normalized


def label_to_key(label: str) -> str:
    """
    Convert an unmapped statement row label into a stable snake_case key.

    Examples:
        "Other Assets" -> "other_assets"
        "Deferred Tax Assets" -> "deferred_tax_assets"
    """
    normalized = normalize_label(label)

    if not normalized:
        return ""

    return normalized.replace(" ", "_")


# ---------------------------------------------------------------------------
# Row type
# ---------------------------------------------------------------------------

def infer_row_type(label: str, has_values: bool = True) -> str:
    """
    Infer the structural type of a financial statement row.

    Allowed values:
        total
        subtotal
        line_item
        heading
    """
    normalized = normalize_label(label)

    if not has_values:
        return "heading"

    if normalized.startswith("total "):
        return "total"

    if normalized.startswith("subtotal "):
        return "subtotal"

    if normalized in {
        "total income",
        "total expenditure",
        "total assets",
        "total liabilities",
        "total equity",
        "total revenue",
        "total expenses",
    }:
        return "total"

    if normalized in PARENT_LABELS:
        return "heading"

    return "line_item"


# ---------------------------------------------------------------------------
# Canonical target helper
# ---------------------------------------------------------------------------

def _target(
    statement: str,
    section: str | None,
    account: str,
) -> CanonicalTarget:
    if section is None:
        return CanonicalTarget(
            statement=statement,
            path=(account,),
        )

    return CanonicalTarget(
        statement=statement,
        path=(section, account),
    )


# ---------------------------------------------------------------------------
# Known semantic mappings
#
# IMPORTANT:
# These are only mappings to concepts that already exist in the canonical
# model or are explicitly approved aliases in the project key inventory.
#
# Genuinely new concepts should continue to fall through to dynamic/
# additional_items handling in the extraction layer.
# ---------------------------------------------------------------------------

CANONICAL_SYNONYMS: dict[CanonicalTarget, tuple[str, ...]] = {

    # =======================================================================
    # BALANCE SHEET — ASSETS
    # =======================================================================

    _target(
        "balance_sheet",
        "assets",
        "cash_and_cash_equivalents",
    ): (
        "Cash and cash equivalents",
        "Cash & cash equivalents",
    ),

    _target(
        "balance_sheet",
        "assets",
        "balances_with_central_bank",
    ): (
        "Balances with central bank",
        "Balances with Central Bank",
    ),

    _target(
        "balance_sheet",
        "assets",
        "balances_with_other_banks",
    ): (
        "Balances with other banks",
        "Balances with Other Banks",
    ),

    _target(
        "balance_sheet",
        "assets",
        "investments",
    ): (
        "Investments",
    ),

    _target(
        "balance_sheet",
        "assets",
        "loans_and_advances",
    ): (
        "Loans and advances",
        "Loans & advances",
        "Advances",
        "Loans",
    ),

    _target(
        "balance_sheet",
        "assets",
        "trade_receivables",
    ): (
        "Trade receivables",
        "Trade receivables and other receivables",
    ),

    _target(
        "balance_sheet",
        "assets",
        "property_plant_equipment",
    ): (
        "Property, plant and equipment",
        "Property plant and equipment",
        "Fixed Assets",
        "Fixed assets",
    ),

    _target(
        "balance_sheet",
        "assets",
        "intangible_assets",
    ): (
        "Intangible assets",
        "Intangible Assets",
    ),

    _target(
        "balance_sheet",
        "assets",
        "deferred_tax_assets",
    ): (
        "Deferred tax assets",
        "Deferred Tax Assets",
    ),

    _target(
        "balance_sheet",
        "assets",
        "other_assets",
    ): (
        "Other assets",
        "Other Assets",
    ),

    _target(
        "balance_sheet",
        "assets",
        "total_assets",
    ): (
        "Total assets",
        "Total Assets",
    ),

    # =======================================================================
    # BALANCE SHEET — LIABILITIES
    # =======================================================================

    _target(
        "balance_sheet",
        "liabilities",
        "deposits_from_customers",
    ): (
        "Deposits from customers",
        "Deposits",
        "Customer deposits",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "borrowings",
    ): (
        "Borrowings",
        "Borrowings from banks",
        "Borrowings from financial institutions",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "other_bank_borrowings",
    ): (
        "Other bank borrowings",
        "Other Bank Borrowings",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "trade_payables",
    ): (
        "Trade payables",
        "Trade Payables",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "tax_liabilities",
    ): (
        "Tax liabilities",
        "Tax Liabilities",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "deferred_tax_liabilities",
    ): (
        "Deferred tax liabilities",
        "Deferred Tax Liabilities",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "provisions",
    ): (
        "Provisions",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "other_liabilities",
    ): (
        "Other liabilities",
        "Other Liabilities",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "total_liabilities",
    ): (
        "Total liabilities",
        "Total Liabilities",
    ),

    # =======================================================================
    # BALANCE SHEET — EQUITY
    # =======================================================================

    _target(
        "balance_sheet",
        "equity",
        "share_capital",
    ): (
        "Share capital",
        "Capital",
        "Issued, Subscribed and Paid-up Capital",
    ),

    _target(
        "balance_sheet",
        "equity",
        "share_premium",
    ): (
        "Share premium",
        "Share Premium",
    ),

    _target(
        "balance_sheet",
        "equity",
        "retained_earnings",
    ): (
        "Retained earnings",
        "Balance in Profit and Loss Account",
    ),

    _target(
        "balance_sheet",
        "equity",
        "other_reserves",
    ): (
        "Other reserves",
        "Other Reserves",
    ),

    _target(
        "balance_sheet",
        "equity",
        "total_equity",
    ): (
        "Total equity",
        "Total Equity",
    ),

    # =======================================================================
    # BALANCE SHEET — MERIDIAN / IND AS VARIANTS
    # =======================================================================

    _target(
        "balance_sheet",
        "assets",
        "bank_balances_other_than_cash_and_cash_equivalents",
    ): (
        "Bank Balances other than Cash and Cash Equivalents",
        "Bank Balances Other than Cash and Cash Equivalents",
    ),

    _target(
        "balance_sheet",
        "assets",
        "other_financial_assets",
    ): (
        "Other Financial Assets",
    ),

    _target(
        "balance_sheet",
        "assets",
        "total_financial_assets",
    ): (
        "Total Financial Assets",
    ),

    _target(
        "balance_sheet",
        "assets",
        "property_plant_equipment",
    ): (
        "Property, Plant and Equipment",
        "Property Plant and Equipment",
    ),

    _target(
        "balance_sheet",
        "assets",
        "intangible_assets",
    ): (
        "Intangible Assets",
    ),

    _target(
        "balance_sheet",
        "assets",
        "deferred_tax_assets",
    ): (
        "Deferred Tax Assets (net)",
        "Deferred Tax Assets",
    ),

    _target(
        "balance_sheet",
        "assets",
        "other_non_financial_assets",
    ): (
        "Other Non-Financial Assets",
        "Other Non Financial Assets",
    ),

    _target(
        "balance_sheet",
        "assets",
        "total_non_financial_assets",
    ): (
        "Total Non-Financial Assets",
        "Total Non Financial Assets",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "debt_securities",
    ): (
        "Debt Securities",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "borrowings_other_than_debt_securities",
    ): (
        "Borrowings (Other than Debt Securities)",
        "Borrowings Other than Debt Securities",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "subordinated_liabilities",
    ): (
        "Subordinated Liabilities",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "other_financial_liabilities",
    ): (
        "Other Financial Liabilities",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "total_financial_liabilities",
    ): (
        "Total Financial Liabilities",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "current_tax_liabilities",
    ): (
        "Current Tax Liabilities (net)",
        "Current Tax Liabilities",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "provisions",
    ): (
        "Provisions",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "other_non_financial_liabilities",
    ): (
        "Other Non-Financial Liabilities",
        "Other Non Financial Liabilities",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "total_non_financial_liabilities",
    ): (
        "Total Non-Financial Liabilities",
        "Total Non Financial Liabilities",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "total_liabilities",
    ): (
        "Total Liabilities",
    ),

    _target(
        "balance_sheet",
        "equity",
        "share_capital",
    ): (
        "Equity Share Capital",
        "Share Capital",
    ),

    _target(
        "balance_sheet",
        "equity",
        "other_equity",
    ): (
        "Other Equity",
    ),

    _target(
        "balance_sheet",
        "equity",
        "total_equity",
    ): (
        "Total Equity",
    ),

    _target(
        "balance_sheet",
        "liabilities",
        "total_liabilities_and_equity",
    ): (
        "Total Liabilities and Equity",
        "Total Liabilities & Equity",
    ),

    # =======================================================================
    # PROFIT & LOSS — INCOME
    # =======================================================================

    _target(
        "profit_and_loss",
        "income",
        "interest_income",
    ): (
        "Interest income",
        "Interest Earned",
    ),

    _target(
        "profit_and_loss",
        "income",
        "fee_and_commission_income",
    ): (
        "Fee and commission income",
        "Fees and commission income",
        "Fee & commission income",
        "Fees & commission income",
    ),

    _target(
        "profit_and_loss",
        "income",
        "trading_income",
    ): (
        "Trading income",
        "Trading Income",
    ),

    _target(
        "profit_and_loss",
        "income",
        "other_operating_income",
    ): (
        "Other operating income",
        "Other Operating Income",
    ),

    _target(
        "profit_and_loss",
        "income",
        "other_income",
    ): (
        "Other income",
        "Other Income",
    ),

    _target(
        "profit_and_loss",
        "income",
        "total_income",
    ): (
        "Total income",
        "Total Income",
        "Total Income (I)",
    ),

    # =======================================================================
    # PROFIT & LOSS — EXPENSES
    # =======================================================================

    _target(
        "profit_and_loss",
        "expenses",
        "interest_expense",
    ): (
        "Interest expense",
        "Interest Expended",
    ),

    _target(
        "profit_and_loss",
        "expenses",
        "employee_expenses",
    ): (
        "Employee expenses",
        "Employee Expenses",
        "Employee Benefits Expenses",
    ),

    _target(
        "profit_and_loss",
        "expenses",
        "depreciation",
    ): (
        "Depreciation",
        "Depreciation and Amortisation",
        "Depreciation and Amortization",
    ),

    _target(
        "profit_and_loss",
        "expenses",
        "administrative_expenses",
    ): (
        "Administrative expenses",
        "Administrative Expenses",
    ),

    _target(
        "profit_and_loss",
        "expenses",
        "provision_for_credit_losses",
    ): (
        "Provision for credit losses",
        "Provision for Credit Losses",
    ),

    _target(
        "profit_and_loss",
        "expenses",
        "other_expenses",
    ): (
        "Other expenses",
        "Other Expenses",
    ),

    _target(
        "profit_and_loss",
        "expenses",
        "total_expenses",
    ): (
        "Total expenses",
        "Total Expenses",
        "Total Expenditure",
        "Total Expenditure (II)",
    ),

    # =======================================================================
    # PROFIT & LOSS — PROFIT
    # =======================================================================

    _target(
        "profit_and_loss",
        "profit",
        "profit_before_tax",
    ): (
        "Profit before tax",
        "Profit Before Tax",
    ),

    _target(
        "profit_and_loss",
        "profit",
        "tax_expense",
    ): (
        "Tax expense",
        "Tax Expense",
        "Tax Expense (Current and Deferred)",
    ),

    _target(
        "profit_and_loss",
        "profit",
        "net_income",
    ): (
        "Net income",
        "Net Income",
        "Net Profit for the year",
        "Net Profit for the year (I - II)",
        "Net Profit for the Year",
        "Profit for the Year (IV - Tax Expense)",
    ),

    # =======================================================================
    # PROFIT & LOSS — MERIDIAN / IND AS VARIANTS
    # =======================================================================

    _target(
        "profit_and_loss",
        "income",
        "net_gain_on_fair_value_changes",
    ): (
        "Net Gain on Fair Value Changes",
        "Net gain on fair value changes",
    ),

    _target(
        "profit_and_loss",
        "income",
        "total_revenue_from_operations",
    ): (
        "Total Revenue from Operations (I)",
        "Total Revenue from Operations",
    ),

    _target(
        "profit_and_loss",
        "expenses",
        "finance_costs",
    ): (
        "Finance Costs",
        "Finance costs",
    ),

    _target(
        "profit_and_loss",
        "expenses",
        "impairment_on_financial_instruments",
    ): (
        "Impairment on Financial Instruments",
        "Impairment on financial instruments",
    ),

    # =======================================================================
    # CASH FLOW — RECONCILIATION
    # =======================================================================

    _target(
        "cash_flow",
        None,
        "opening_cash",
    ): (
        "Opening cash",
        "Cash and Cash Equivalents at the Beginning of the Year",
        "Cash and cash equivalents at beginning of year",
    ),

    _target(
        "cash_flow",
        None,
        "net_change_in_cash",
    ): (
        "Net change in cash",
        "Net Change in Cash",
        "Net increase / decrease in cash",
        "Net increase in cash",
        "Net decrease in cash",
    ),

    _target(
        "cash_flow",
        None,
        "closing_cash",
    ): (
        "Closing cash",
        "Cash and Cash Equivalents at the End of the Year",
        "Cash and cash equivalents at end of year",
    ),

    # =======================================================================
    # CASH FLOW — OPERATING ACTIVITIES
    # =======================================================================

    _target(
        "cash_flow",
        None,
        "net_income",
    ): (
        "Net income",
        "Net Income",
    ),

    _target(
        "cash_flow",
        None,
        "depreciation",
    ): (
        "Depreciation",
        "Depreciation and Amortisation",
        "Depreciation and Amortization",
    ),

    _target(
        "cash_flow",
        None,
        "provision_adjustments",
    ): (
        "Provision adjustments",
        "Provision adjustment",
        "Provision adjustments",
        "Adjustments for provisions",
    ),

    _target(
        "cash_flow",
        None,
        "working_capital_changes",
    ): (
        "Working capital changes",
        "Changes in working capital",
        "Working Capital Changes",
    ),

    _target(
        "cash_flow",
        None,
        "other_operating_adjustments",
    ): (
        "Other operating adjustments",
        "Other Operating Adjustments",
    ),

    _target(
        "cash_flow",
        None,
        "net_cash_from_operating_activities",
    ): (
        "Net cash from operating activities",
        "Net Cash Generated from / (Used in) Operating Activities",
        "Net Cash from Operating Activities",
    ),

    # =======================================================================
    # CASH FLOW — INVESTING ACTIVITIES
    # =======================================================================

    _target(
        "cash_flow",
        None,
        "purchase_of_investments",
    ): (
        "Purchase of investments",
        "Purchase of Investments",
    ),

    _target(
        "cash_flow",
        None,
        "sale_of_investments",
    ): (
        "Sale of investments",
        "Sale of Investments",
    ),

    _target(
        "cash_flow",
        None,
        "purchase_of_property",
    ): (
        "Purchase of property, plant and equipment",
        "Purchase of Property, Plant and Equipment",
        "(Purchase of Property, Plant and Equipment)",
    ),

    _target(
        "cash_flow",
        None,
        "purchase_of_intangible_assets",
    ): (
        "Purchase of intangible assets",
        "Purchase of Intangible Assets",
        "(Purchase of Intangible Assets)",
    ),

    _target(
        "cash_flow",
        None,
        "sale_of_property",
    ): (
        "Sale of property, plant and equipment",
        "Sale of Property, Plant and Equipment",
    ),

    _target(
        "cash_flow",
        None,
        "other_investing_cash_flows",
    ): (
        "Other investing cash flows",
        "Other Investing Cash Flows",
    ),

    _target(
        "cash_flow",
        None,
        "net_cash_from_investing_activities",
    ): (
        "Net cash from investing activities",
        "Net Cash Used in Investing Activities",
        "Net Cash from Investing Activities",
    ),

    # =======================================================================
    # CASH FLOW — FINANCING ACTIVITIES
    # =======================================================================

    _target(
        "cash_flow",
        None,
        "proceeds_from_borrowings",
    ): (
        "Proceeds from borrowings",
        "Proceeds from Borrowings",
    ),

    _target(
        "cash_flow",
        None,
        "repayment_of_borrowings",
    ): (
        "Repayment of borrowings",
        "Repayment of Borrowings",
    ),

    _target(
        "cash_flow",
        None,
        "dividends_paid",
    ): (
        "Dividends paid",
        "Dividends Paid",
    ),

    _target(
        "cash_flow",
        None,
        "share_capital_issued",
    ): (
        "Share capital issued",
        "Share Capital Issued",
    ),

    _target(
        "cash_flow",
        None,
        "other_financing_cash_flows",
    ): (
        "Other financing cash flows",
        "Other Financing Cash Flows",
    ),

    _target(
        "cash_flow",
        None,
        "net_cash_from_financing_activities",
    ): (
        "Net cash from financing activities",
        "Net Cash from Financing Activities",
    ),

    # =======================================================================
    # CASH FLOW — MERIDIAN / IND AS VARIANTS
    # =======================================================================

    _target(
        "cash_flow",
        "operating_activities",
        "net_income",
    ): (
        "Profit for the Year",
        "Profit for the year",
    ),

    _target(
        "cash_flow",
        "operating_activities",
        "increase_in_loans",
    ): (
        "(Increase) in Loans",
        "Increase in Loans",
    ),

    _target(
        "cash_flow",
        "operating_activities",
        "increase_in_investments",
    ): (
        "(Increase) in Investments",
        "Increase in Investments",
    ),

    _target(
        "cash_flow",
        "operating_activities",
        "increase_in_other_financial_assets",
    ): (
        "(Increase) in Other Financial Assets",
        "Increase in Other Financial Assets",
    ),

    _target(
        "cash_flow",
        "operating_activities",
        "increase_in_bank_balances_other_than_cash_and_cash_equivalents",
    ): (
        "(Increase) in Bank Balances other than Cash and Cash Equivalents",
        "Increase in Bank Balances other than Cash and Cash Equivalents",
    ),

    _target(
        "cash_flow",
        "operating_activities",
        "increase_in_other_non_financial_assets",
    ): (
        "(Increase) in Other Non-Financial Assets",
        "Increase in Other Non-Financial Assets",
    ),

    _target(
        "cash_flow",
        "operating_activities",
        "increase_in_deferred_tax_assets",
    ): (
        "(Increase) in Deferred Tax Assets",
        "Increase in Deferred Tax Assets",
    ),

    _target(
        "cash_flow",
        "operating_activities",
        "increase_in_trade_payables",
    ): (
        "Increase in Trade Payables",
    ),

    _target(
        "cash_flow",
        "operating_activities",
        "increase_in_other_financial_liabilities",
    ): (
        "Increase in Other Financial Liabilities",
    ),

    _target(
        "cash_flow",
        "operating_activities",
        "increase_in_current_tax_liabilities",
    ): (
        "Increase in Current Tax Liabilities",
    ),

    _target(
        "cash_flow",
        "operating_activities",
        "increase_in_provisions",
    ): (
        "Increase in Provisions",
    ),

    _target(
        "cash_flow",
        "operating_activities",
        "increase_in_other_non_financial_liabilities",
    ): (
        "Increase in Other Non-Financial Liabilities",
    ),

    _target(
        "cash_flow",
        "operating_activities",
        "net_cash_from_operating_activities",
    ): (
        "Net Cash Generated from / (Used in) Operating Activities",
        "Net Cash from Operating Activities",
    ),

    _target(
        "cash_flow",
        "investing_activities",
        "net_cash_from_investing_activities",
    ): (
        "Net Cash Used in Investing Activities",
        "Net Cash from Investing Activities",
    ),

    _target(
        "cash_flow",
        "financing_activities",
        "increase_in_debt_securities",
    ): (
        "Increase in Debt Securities",
    ),

    _target(
        "cash_flow",
        "financing_activities",
        "increase_in_borrowings",
    ): (
        "Increase in Borrowings (Other than Debt Securities)",
        "Increase in Borrowings other than Debt Securities",
        "Increase in Borrowings",
    ),

    _target(
        "cash_flow",
        "financing_activities",
        "increase_in_subordinated_liabilities",
    ): (
        "Increase in Subordinated Liabilities",
    ),

    _target(
        "cash_flow",
        "financing_activities",
        "net_cash_from_financing_activities",
    ): (
        "Net Cash from Financing Activities",
    ),

    _target(
        "cash_flow",
        None,
        "net_change_in_cash",
    ): (
        "Net Increase / (Decrease) in Cash and Cash Equivalents",
        "Net Increase / (Decrease) in Cash and Cash Equivalents (A + B + C)",
        "Net Increase in Cash and Cash Equivalents",
        "Net change in cash",
    ),

    _target(
        "cash_flow",
        None,
        "opening_cash",
    ): (
        "Cash and Cash Equivalents at the Beginning of the Year (Note 3, PY)",
        "Cash and Cash Equivalents at the Beginning of the Year",
        "Opening cash",
    ),

    _target(
        "cash_flow",
        None,
        "closing_cash",
    ): (
        "Cash and Cash Equivalents at the End of the Year (Note 3, CY)",
        "Cash and Cash Equivalents at the End of the Year",
        "Closing cash",
    ),

    # =======================================================================
    # EQUITY STATEMENT
    # =======================================================================

    _target(
        "equity",
        None,
        "opening_equity",
    ): (
        "Opening equity",
        "Opening Equity",
    ),

    _target(
        "equity",
        None,
        "net_income",
    ): (
        "Net income",
        "Net Income",
    ),

    _target(
        "equity",
        None,
        "share_capital_issued",
    ): (
        "Share capital issued",
        "Share Capital Issued",
    ),

    _target(
        "equity",
        None,
        "other_equity_movements",
    ): (
        "Other equity movements",
        "Other Equity Movements",
    ),

    _target(
        "equity",
        None,
        "dividends_paid",
    ): (
        "Dividends paid",
        "Dividends Paid",
    ),

    _target(
        "equity",
        None,
        "closing_equity",
    ): (
        "Closing equity",
        "Closing Equity",
    ),

    # =======================================================================
    # NOTES
    # =======================================================================

    _target(
        "notes",
        None,
        "note_12_cash",
    ): (
        "Cash and Cash Equivalents",
        "Cash and cash equivalents",
    ),
}


# ---------------------------------------------------------------------------
# Lookup table
# ---------------------------------------------------------------------------

LABEL_TO_TARGETS: dict[str, list[CanonicalTarget]] = {}

for target, synonyms in CANONICAL_SYNONYMS.items():
    for synonym in synonyms:
        normalized = normalize_label(synonym)

        if not normalized:
            continue

        targets = LABEL_TO_TARGETS.setdefault(normalized, [])

        if target not in targets:
            targets.append(target)


# ---------------------------------------------------------------------------
# Label mapping
# ---------------------------------------------------------------------------

def map_label(
    label: str,
    statement: str | None = None,
) -> CanonicalTarget | None:
    """
    Map a known source label to an existing canonical target.

    Mapping is statement-aware.

    Example:
        "Net income" + "profit_and_loss"
            -> profit_and_loss / profit / net_income

        "Net income" + "cash_flow"
            -> cash_flow / net_income

        "Net income" + "equity"
            -> equity / net_income

    This prevents the same source label from being mapped to the wrong
    statement when the label is legitimately reused across statements.
    """
    normalized = normalize_label(label)

    if not normalized:
        return None

    targets = LABEL_TO_TARGETS.get(normalized, [])

    if not targets:
        return None

    if statement is not None:
        statement_targets = [
            target
            for target in targets
            if target.statement == statement
        ]

        if len(statement_targets) == 1:
            return statement_targets[0]

        # Multiple targets within the same statement means the mapping is
        # ambiguous. Do not guess.
        if len(statement_targets) > 1:
            return None

        return None

    # Without statement context, only return a target if the label maps
    # uniquely across the entire canonical model.
    if len(targets) == 1:
        return targets[0]

    return None


# ---------------------------------------------------------------------------
# Section inference
# ---------------------------------------------------------------------------

SECTION_ALIASES: dict[str, dict[str, str]] = {

    "balance_sheet": {
        "assets": "assets",

        "capital and liabilities": "liabilities",
        "liabilities": "liabilities",

        "equity": "equity",
        "shareholders equity": "equity",
        "shareholders funds": "equity",

        "current assets": "assets",
        "financial assets": "assets",
        "non financial assets": "assets",

        "financial liabilities": "liabilities",
        "non financial liabilities": "liabilities",
    },

    "profit_and_loss": {
        "i income": "income",
        "income": "income",

        "i revenue from operations": "income",
        "ii other income": "income",

        "ii expenditure": "expenses",
        "expenditure": "expenses",
        "expenses": "expenses",

        "iii expenses": "expenses",

        "iii profit loss": "profit",
        "profit loss": "profit",
        "profit and loss": "profit",
        "profit": "profit",
    },

    "cash_flow": {
        "a cash flow from operating activities": "operating_activities",
        "cash flow from operating activities": "operating_activities",

        "b cash flow from investing activities": "investing_activities",
        "cash flow from investing activities": "investing_activities",

        "c cash flow from financing activities": "financing_activities",
        "cash flow from financing activities": "financing_activities",

        "reconciliation": "reconciliation",
    },

    "equity": {},

    "notes": {},

    "schedules": {
        "particulars": "particulars",
    },
}


def section_from_label(
    label: str,
    statement: str | None,
) -> str | None:
    """
    Return the canonical section represented by a heading label.

    Returns None when the label is not a recognized section heading.
    """
    if statement is None:
        return None

    normalized = normalize_label(label)

    aliases = SECTION_ALIASES.get(statement, {})

    return aliases.get(normalized)


# ---------------------------------------------------------------------------
# Structural heading detection
# ---------------------------------------------------------------------------

def is_parent_label(label: str) -> bool:
    """Return True when the label is a structural heading."""
    return normalize_label(label) in PARENT_LABELS
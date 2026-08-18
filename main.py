import json
import os
import sys

from engine.consistency_engine import (
    check_cash_consistency,
    check_cash_flow_vs_notes,
    check_balance_sheet_vs_notes,
    check_equity_rollforward,
    check_depreciation_vs_notes,
    check_tax_vs_notes,
    check_dividends_vs_notes
)

from engine.prior_year_engine import (
    check_cash_prior_year,
    check_assets_prior_year,
    check_liabilities_prior_year,
    check_equity_prior_year,
    check_net_income_prior_year,
    check_depreciation_prior_year,
    check_tax_prior_year,
    check_dividends_prior_year
)

from engine.member5_summary import summarize_member5_results


def run_member5_pipeline(data_path="data/final_financial_data.json"):
    """
    Execute the complete Member 5 review pipeline:
    1. Load financial data
    2. Run Consistency checks (C001-C007)
    3. Run Prior-Year checks (PY001-PY008)
    4. Aggregate findings
    5. Generate Member 5 summary metrics
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Financial data file not found at: {data_path}")

    with open(data_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # 1. Execute Consistency Rules (7 rules)
    consistency_results = [
        check_cash_consistency(data),
        check_cash_flow_vs_notes(data),
        check_balance_sheet_vs_notes(data),
        check_equity_rollforward(data),
        check_depreciation_vs_notes(data),
        check_tax_vs_notes(data),
        check_dividends_vs_notes(data)
    ]

    # 2. Execute Prior-Year Movement Rules (8 rules)
    prior_year_results = [
        check_cash_prior_year(data),
        check_assets_prior_year(data),
        check_liabilities_prior_year(data),
        check_equity_prior_year(data),
        check_net_income_prior_year(data),
        check_depreciation_prior_year(data),
        check_tax_prior_year(data),
        check_dividends_prior_year(data)
    ]

    # 3. Combine all 15 findings
    all_findings = consistency_results + prior_year_results

    # 4. Generate structured summary
    output = summarize_member5_results(all_findings)
    output["data_source"] = data_path

    return output


def print_report(output):
    """
    Print a clean, professional console report for Member 5 results.
    """
    summary = output["summary"]
    consistency = output["consistency"]
    prior_year = output["prior_year"]
    findings = output["findings"]
    data_source = output.get("data_source", "Unknown")

    print("\n" + "=" * 70)
    print(" AUDIT-LENS | MEMBER 5: CONSISTENCY + PRIOR-YEAR ENGINE")
    print("=" * 70)
    print(f"Data Source: {data_source}")
    print("-" * 70)

    print("\n--- EXECUTIVE SUMMARY ---")
    print(f"  Total Rules Executed : {summary['total_rules']}")
    print(f"  PASS                 : {summary['pass']}")
    print(f"  FAIL                 : {summary['fail']}")
    print(f"  UNUSUAL              : {summary['unusual']}")
    print(f"  REVIEW               : {summary['review']}")

    print("\n--- MODULE BREAKDOWN ---")
    print(f"  [Consistency Analysis] Total: {consistency['total_rules']} | PASS: {consistency['pass']} | FAIL: {consistency['fail']} | REVIEW: {consistency['review']}")
    print(f"  [Prior-Year Analysis] Total: {prior_year['total_rules']} | PASS: {prior_year['pass']} | UNUSUAL: {prior_year['unusual']} | REVIEW: {prior_year['review']}")

    print("\n--- DETAILED FINDINGS (15 RULES) ---")
    print(f"{'Rule ID':<8} {'Category':<14} {'Status':<10} {'Severity':<10} {'Message'}")
    print("-" * 70)

    for f in findings:
        rule_id = f.get("rule_id", "N/A")
        category = f.get("category", "N/A")
        status = f.get("status", "N/A")
        severity = f.get("severity", "N/A")
        message = f.get("message", "")
        print(f"{rule_id:<8} {category:<14} {status:<10} {severity:<10} {message}")

    print("=" * 70 + "\n")


def main():
    data_file = sys.argv[1] if len(sys.argv) > 1 else "data/final_financial_data.json"
    output = run_member5_pipeline(data_file)
    print_report(output)
    return output


if __name__ == "__main__":
    main()
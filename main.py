import json

from engine.consistency_engine import (
    check_cash_consistency,
    check_cash_flow_vs_notes,
    check_balance_sheet_vs_notes,
    check_depreciation_vs_notes,
    check_tax_vs_notes,
    check_dividends_vs_notes,
    check_equity_rollforward
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

with open("data/mock_financial_data.json", "r") as file:
    data = json.load(file)


results = [
    #Consistency checks
    check_cash_consistency(data),
    check_cash_flow_vs_notes(data),
    check_balance_sheet_vs_notes(data),
    check_equity_rollforward(data),
    check_depreciation_vs_notes(data),
    check_tax_vs_notes(data),
    check_dividends_vs_notes(data),

    #Prior year checks
    check_cash_prior_year(data),
    check_assets_prior_year(data),
    check_liabilities_prior_year(data),
    check_equity_prior_year(data),
    check_net_income_prior_year(data),
    check_depreciation_prior_year(data),
    check_tax_prior_year(data),
    check_dividends_prior_year(data)
]


member5_output = summarize_member5_results(results)

print("\n===== MEMBER 5 SUMMARY =====")
print(member5_output["summary"])

print("\n===== CONSISTENCY SUMMARY =====")
print(member5_output["consistency"])

print("\n===== PRIOR-YEAR SUMMARY =====")
print(member5_output["prior_year"])

print("\n===== FINDINGS =====")
for finding in member5_output["findings"]:
    print(finding)
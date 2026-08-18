import json
import os
import sys
import copy
import unittest

# Allow Python to find the engine package
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

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


class TestMember5Engine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        data_path = os.path.join(
            PROJECT_ROOT,
            "data",
            "mock_financial_data.json"
        )

        with open(data_path, "r") as file:
            cls.data = json.load(file)

    # ---------------------------------------------------------
    # CONSISTENCY TESTS
    # ---------------------------------------------------------

    def test_c001_cash_consistency(self):
        result = check_cash_consistency(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "C001")
        self.assertEqual(result["status"], "PASS")

    def test_c002_cash_flow_vs_notes(self):
        result = check_cash_flow_vs_notes(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "C002")
        self.assertEqual(result["status"], "PASS")

    def test_c003_balance_sheet_vs_notes(self):
        result = check_balance_sheet_vs_notes(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "C003")
        self.assertEqual(result["status"], "PASS")

    def test_c004_equity_rollforward(self):
        result = check_equity_rollforward(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "C004")
        self.assertEqual(result["status"], "PASS")

    def test_c005_depreciation_vs_notes(self):
        result = check_depreciation_vs_notes(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "C005")
        self.assertEqual(result["status"], "PASS")

    def test_c006_tax_vs_notes(self):
        result = check_tax_vs_notes(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "C006")
        self.assertEqual(result["status"], "PASS")

    def test_c007_dividends_vs_notes(self):
        result = check_dividends_vs_notes(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "C007")
        self.assertEqual(result["status"], "PASS")

    # ---------------------------------------------------------
    # PRIOR-YEAR TESTS
    # ---------------------------------------------------------

    def test_py001_cash_prior_year(self):
        result = check_cash_prior_year(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "PY001")
        self.assertEqual(result["status"], "UNUSUAL")

    def test_py002_assets_prior_year(self):
        result = check_assets_prior_year(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "PY002")
        self.assertEqual(result["status"], "PASS")

    def test_py003_liabilities_prior_year(self):
        result = check_liabilities_prior_year(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "PY003")
        self.assertEqual(result["status"], "PASS")

    def test_py004_equity_prior_year(self):
        result = check_equity_prior_year(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "PY004")
        self.assertEqual(result["status"], "PASS")

    def test_py005_net_income_prior_year(self):
        result = check_net_income_prior_year(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "PY005")
        self.assertEqual(result["status"], "UNUSUAL")

    def test_py006_depreciation_prior_year(self):
        result = check_depreciation_prior_year(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "PY006")
        self.assertEqual(result["status"], "PASS")

    def test_py007_tax_prior_year(self):
        result = check_tax_prior_year(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "PY007")
        self.assertEqual(result["status"], "PASS")

    def test_py008_dividends_prior_year(self):
        result = check_dividends_prior_year(copy.deepcopy(self.data))
        self.assertEqual(result["rule_id"], "PY008")
        self.assertEqual(result["status"], "UNUSUAL")

    # ---------------------------------------------------------
    # NEGATIVE / EDGE-CASE TESTS
    # ---------------------------------------------------------

    def test_c002_cash_flow_notes_mismatch(self):
        data = copy.deepcopy(self.data)
        data["notes"]["cash"] = 6000
        result = check_cash_flow_vs_notes(data)
        self.assertEqual(result["rule_id"], "C002")
        self.assertEqual(result["status"], "FAIL")

    def test_c003_balance_sheet_notes_mismatch(self):
        data = copy.deepcopy(self.data)
        data["notes"]["cash"] = 6000
        result = check_balance_sheet_vs_notes(data)
        self.assertEqual(result["rule_id"], "C003")
        self.assertEqual(result["status"], "FAIL")

    def test_c004_equity_rollforward_mismatch(self):
        data = copy.deepcopy(self.data)
        data["balance_sheet"]["total_equity"] = 9000
        result = check_equity_rollforward(data)
        self.assertEqual(result["rule_id"], "C004")
        self.assertEqual(result["status"], "FAIL")

    def test_c005_depreciation_notes_mismatch(self):
        data = copy.deepcopy(self.data)
        data["notes"]["depreciation"] = 700
        result = check_depreciation_vs_notes(data)
        self.assertEqual(result["rule_id"], "C005")
        self.assertEqual(result["status"], "FAIL")

    def test_c006_tax_notes_mismatch(self):
        data = copy.deepcopy(self.data)
        data["notes"]["tax_expense"] = 900
        result = check_tax_vs_notes(data)
        self.assertEqual(result["rule_id"], "C006")
        self.assertEqual(result["status"], "FAIL")

    def test_c007_dividends_notes_mismatch(self):
        data = copy.deepcopy(self.data)
        data["notes"]["dividends"] = 1500
        result = check_dividends_vs_notes(data)
        self.assertEqual(result["rule_id"], "C007")
        self.assertEqual(result["status"], "FAIL")

    def test_py002_large_asset_movement(self):
        data = copy.deepcopy(self.data)
        data["prior_year_data"]["balance_sheet"]["total_assets"] = 25000
        result = check_assets_prior_year(data)
        self.assertEqual(result["rule_id"], "PY002")
        self.assertEqual(result["status"], "UNUSUAL")

    def test_py003_large_liability_movement(self):
        data = copy.deepcopy(self.data)
        data["prior_year_data"]["balance_sheet"]["total_liabilities"] = 25000
        result = check_liabilities_prior_year(data)
        self.assertEqual(result["rule_id"], "PY003")
        self.assertEqual(result["status"], "UNUSUAL")

    def test_py004_large_equity_movement(self):
        data = copy.deepcopy(self.data)
        data["prior_year_data"]["balance_sheet"]["total_equity"] = 4000
        result = check_equity_prior_year(data)
        self.assertEqual(result["rule_id"], "PY004")
        self.assertEqual(result["status"], "UNUSUAL")

    def test_py002_zero_prior_year_assets(self):
        data = copy.deepcopy(self.data)
        data["prior_year_data"]["balance_sheet"]["total_assets"] = 0
        result = check_assets_prior_year(data)
        self.assertEqual(result["rule_id"], "PY002")
        self.assertEqual(result["status"], "REVIEW")

    def test_py003_zero_prior_year_liabilities(self):
        data = copy.deepcopy(self.data)
        data["prior_year_data"]["balance_sheet"]["total_liabilities"] = 0
        result = check_liabilities_prior_year(data)
        self.assertEqual(result["rule_id"], "PY003")
        self.assertEqual(result["status"], "REVIEW")

    def test_py004_zero_prior_year_equity(self):
        data = copy.deepcopy(self.data)
        data["prior_year_data"]["balance_sheet"]["total_equity"] = 0
        result = check_equity_prior_year(data)
        self.assertEqual(result["rule_id"], "PY004")
        self.assertEqual(result["status"], "REVIEW")

    # ---------------------------------------------------------
    # SUMMARY TEST
    # ---------------------------------------------------------

    def test_member5_summary(self):
        results = [
            check_cash_consistency(copy.deepcopy(self.data)),
            check_cash_flow_vs_notes(copy.deepcopy(self.data)),
            check_balance_sheet_vs_notes(copy.deepcopy(self.data)),
            check_equity_rollforward(copy.deepcopy(self.data)),
            check_depreciation_vs_notes(copy.deepcopy(self.data)),
            check_tax_vs_notes(copy.deepcopy(self.data)),
            check_dividends_vs_notes(copy.deepcopy(self.data)),

            check_cash_prior_year(copy.deepcopy(self.data)),
            check_assets_prior_year(copy.deepcopy(self.data)),
            check_liabilities_prior_year(copy.deepcopy(self.data)),
            check_equity_prior_year(copy.deepcopy(self.data)),
            check_net_income_prior_year(copy.deepcopy(self.data)),
            check_depreciation_prior_year(copy.deepcopy(self.data)),
            check_tax_prior_year(copy.deepcopy(self.data)),
            check_dividends_prior_year(copy.deepcopy(self.data))
        ]

        summary = summarize_member5_results(results)

        self.assertEqual(summary["summary"]["total_rules"], 15)
        self.assertEqual(summary["summary"]["pass"], 12)
        self.assertEqual(summary["summary"]["unusual"], 3)
        self.assertEqual(summary["summary"]["review"], 0)
        self.assertEqual(summary["summary"]["fail"], 0)


class TestMember5FinalData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        data_path = os.path.join(
            PROJECT_ROOT,
            "data",
            "final_financial_data.json"
        )

        with open(data_path, "r", encoding="utf-8") as file:
            cls.final_data = json.load(file)

    def test_final_prior_year_rules(self):
        r_py001 = check_cash_prior_year(self.final_data)
        self.assertEqual(r_py001["rule_id"], "PY001")
        self.assertEqual(r_py001["status"], "UNUSUAL")

        r_py002 = check_assets_prior_year(self.final_data)
        self.assertEqual(r_py002["rule_id"], "PY002")
        self.assertEqual(r_py002["status"], "PASS")

        r_py003 = check_liabilities_prior_year(self.final_data)
        self.assertEqual(r_py003["rule_id"], "PY003")
        self.assertEqual(r_py003["status"], "PASS")

        r_py004 = check_equity_prior_year(self.final_data)
        self.assertEqual(r_py004["rule_id"], "PY004")
        self.assertEqual(r_py004["status"], "PASS")

        r_py005 = check_net_income_prior_year(self.final_data)
        self.assertEqual(r_py005["rule_id"], "PY005")
        self.assertEqual(r_py005["status"], "PASS")

        r_py006 = check_depreciation_prior_year(self.final_data)
        self.assertEqual(r_py006["rule_id"], "PY006")
        self.assertEqual(r_py006["status"], "PASS")

        r_py007 = check_tax_prior_year(self.final_data)
        self.assertEqual(r_py007["rule_id"], "PY007")
        self.assertEqual(r_py007["status"], "PASS")

        r_py008 = check_dividends_prior_year(self.final_data)
        self.assertEqual(r_py008["rule_id"], "PY008")
        self.assertEqual(r_py008["status"], "REVIEW")

    def test_final_consistency_graceful_review(self):
        consistency_checks = [
            check_cash_consistency,
            check_cash_flow_vs_notes,
            check_balance_sheet_vs_notes,
            check_equity_rollforward,
            check_depreciation_vs_notes,
            check_tax_vs_notes,
            check_dividends_vs_notes
        ]
        for check_func in consistency_checks:
            result = check_func(self.final_data)
            self.assertEqual(result["category"], "consistency")
            self.assertEqual(result["status"], "REVIEW")

    def test_final_summary_pipeline(self):
        results = [
            check_cash_consistency(self.final_data),
            check_cash_flow_vs_notes(self.final_data),
            check_balance_sheet_vs_notes(self.final_data),
            check_equity_rollforward(self.final_data),
            check_depreciation_vs_notes(self.final_data),
            check_tax_vs_notes(self.final_data),
            check_dividends_vs_notes(self.final_data),
            check_cash_prior_year(self.final_data),
            check_assets_prior_year(self.final_data),
            check_liabilities_prior_year(self.final_data),
            check_equity_prior_year(self.final_data),
            check_net_income_prior_year(self.final_data),
            check_depreciation_prior_year(self.final_data),
            check_tax_prior_year(self.final_data),
            check_dividends_prior_year(self.final_data)
        ]
        summary = summarize_member5_results(results)
        self.assertEqual(summary["summary"]["total_rules"], 15)
        self.assertEqual(summary["summary"]["pass"], 6)
        self.assertEqual(summary["summary"]["unusual"], 1)
        self.assertEqual(summary["summary"]["review"], 8)
        self.assertEqual(summary["summary"]["fail"], 0)


if __name__ == "__main__":
    unittest.main()
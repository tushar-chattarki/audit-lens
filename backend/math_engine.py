"""
Math Engine for Banking Financial Statement Review
Performs deterministic mathematical checks on canonical JSON data

"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Finding:
    """Standard finding object for all check results"""
    finding_id: str
    module: str
    check: str
    status: str  # "pass", "exception", "not_applicable"
    severity: str  # "high", "medium", "low"
    expected: Optional[float]
    actual: Optional[float]
    difference: Optional[float]
    evidence: List[Dict[str, Any]]
    ai_explanation: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MathEngine:
    """
    Deterministic math engine for banking financial statements.
    Performs all calculations with Python, no LLM involvement.
    """
    
    def __init__(self, materiality_threshold_pct: float = 0.01):
        """
        Initialize the math engine.
        
        Args:
            materiality_threshold_pct: Threshold for rounding differences (as decimal)
        """
        self.materiality_threshold_pct = materiality_threshold_pct
        self.findings: List[Finding] = []
        
    def run(self, canonical_data: Dict[str, Any]) -> List[Finding]:
        """
        Run all math engine checks on the canonical data.
        
        Args:
            canonical_data: The normalized financial data JSON
            
        Returns:
            List of Finding objects
        """
        self.findings = []
        
        # Extract data
        statements = canonical_data.get("statements", {})
        balance_sheet = statements.get("balance_sheet", {})
        profit_loss = statements.get("profit_and_loss", {})
        cash_flow = statements.get("cash_flow", {})
        equity = statements.get("equity", {})
        
        periods = canonical_data.get("periods", ["FY2025", "FY2024"])
        
        logger.info("="*60)
        logger.info(f"Running Math Engine for {canonical_data.get('bank_id', 'Unknown')}")
        logger.info(f"Bank: {canonical_data.get('bank_name', 'Unknown')}")
        logger.info(f"Periods: {periods}")
        logger.info(f"Currency: {canonical_data.get('currency', 'INR')} {canonical_data.get('unit', 'crore')}")
        logger.info("="*60)
        
        # 1. Balance Sheet Checks
        self._check_balance_sheet_identity(balance_sheet, periods)
        
        # 2. P&L Checks
        self._check_profit_loss_identity(profit_loss, periods)
        
        # 3. Cash Flow Checks
        self._check_cash_flow_identity(cash_flow, periods)
        
        # 4. Equity Roll-Forward Checks
        self._check_equity_rollforward(equity, profit_loss, periods)
        
        # 5. Subtotal/Footing Checks
        self._check_subtotals(balance_sheet, profit_loss, periods)
        
        # Print summary
        self._print_summary()
        
        logger.info(f"Math engine completed with {len(self.findings)} findings")
        return self.findings
    
    def _get_value(self, data: Dict, key: str, period: str) -> Optional[float]:
        """Safely extract a value from the data structure."""
        try:
            if key in data:
                period_data = data[key].get(period, {})
                return period_data.get("value")
        except (KeyError, AttributeError, TypeError):
            pass
        return None
    
    def _get_evidence(self, data: Dict, key: str, period: str) -> Optional[Dict]:
        """Safely extract evidence from the data structure."""
        try:
            if key in data:
                period_data = data[key].get(period, {})
                return period_data.get("evidence")
        except (KeyError, AttributeError, TypeError):
            pass
        return None
    
    def _create_finding(self, check: str, status: str, severity: str,
                        expected: Optional[float], actual: Optional[float],
                        evidence_list: List[Dict]) -> Finding:
        """Create a standardized finding object."""
        finding_id = f"math_{uuid.uuid4().hex[:8]}"
        difference = None
        if expected is not None and actual is not None:
            difference = actual - expected
            
        return Finding(
            finding_id=finding_id,
            module="math_engine",
            check=check,
            status=status,
            severity=severity,
            expected=expected,
            actual=actual,
            difference=difference,
            evidence=evidence_list
        )
    
    def _print_summary(self):
        """Print summary of findings."""
        passes = [f for f in self.findings if f.status == 'pass']
        exceptions = [f for f in self.findings if f.status == 'exception']
        not_applicable = [f for f in self.findings if f.status == 'not_applicable']
        
        logger.info("="*60)
        logger.info("MATH ENGINE FINDINGS SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Checks: {len(self.findings)}")
        logger.info(f"   Pass: {len(passes)}")
        logger.info(f"   Exceptions: {len(exceptions)}")
        logger.info(f"   Not Applicable: {len(not_applicable)}")
        logger.info("="*60)
        
        if exceptions:
            logger.info("\nEXCEPTIONS:")
            for f in exceptions:
                logger.info(f"  • {f.check}")
                logger.info(f"    Expected: {f.expected}, Actual: {f.actual}, Diff: {f.difference}")
                logger.info(f"    Severity: {f.severity}")
    
    def _check_balance_sheet_identity(self, balance_sheet: Dict, periods: List[str]):
        """
        Check: Total Assets = Total Liabilities + Total Equity
        The fundamental accounting equation.
        
        FIXED: Now properly looks for data at root level
        """
        logger.info("Checking Balance Sheet identity...")
        
        for period in periods:
            # Try to get values from different locations
            # 1. Try root level (where your data has it)
            total_assets = balance_sheet.get("total_assets", {}).get(period, {}).get("value")
            total_liabilities = balance_sheet.get("total_liabilities", {}).get(period, {}).get("value")
            total_equity = balance_sheet.get("total_equity", {}).get(period, {}).get("value")
            
            # 2. If not found, try assets/liabilities/equity sub-objects
            if total_assets is None:
                total_assets = self._get_value(balance_sheet.get("assets", {}), "total_assets", period)
            if total_liabilities is None:
                total_liabilities = self._get_value(balance_sheet.get("liabilities", {}), "total_liabilities", period)
            if total_equity is None:
                total_equity = self._get_value(balance_sheet.get("equity", {}), "total_equity", period)
            
            # Get evidence from same locations
            assets_evidence = balance_sheet.get("total_assets", {}).get(period, {}).get("evidence")
            if assets_evidence is None:
                assets_evidence = self._get_evidence(balance_sheet.get("assets", {}), "total_assets", period)
            
            liabilities_evidence = balance_sheet.get("total_liabilities", {}).get(period, {}).get("evidence")
            if liabilities_evidence is None:
                liabilities_evidence = self._get_evidence(balance_sheet.get("liabilities", {}), "total_liabilities", period)
            
            equity_evidence = balance_sheet.get("total_equity", {}).get(period, {}).get("evidence")
            if equity_evidence is None:
                equity_evidence = self._get_evidence(balance_sheet.get("equity", {}), "total_equity", period)
            
            evidence_list = [e for e in [assets_evidence, liabilities_evidence, equity_evidence] if e]
            
            # Check if all values are available
            if None in (total_assets, total_liabilities, total_equity):
                self.findings.append(self._create_finding(
                    check=f"balance_sheet_identity_{period}",
                    status="not_applicable",
                    severity="low",
                    expected=None,
                    actual=None,
                    evidence_list=evidence_list
                ))
                logger.info(f"  {period}: NOT_APPLICABLE - Missing data")
                continue
            
            # Calculate expected total
            expected_total = total_liabilities + total_equity
            difference = total_assets - expected_total
            
            # Check if within materiality threshold
            if abs(difference) / max(abs(expected_total), 1) <= self.materiality_threshold_pct:
                status = "pass"
                severity = "low"
            else:
                status = "exception"
                severity = "high" if abs(difference) > 100 else "medium"
            
            self.findings.append(self._create_finding(
                check=f"balance_sheet_identity_{period}",
                status=status,
                severity=severity,
                expected=expected_total,
                actual=total_assets,
                evidence_list=evidence_list
            ))
            
            if status == "exception":
                logger.warning(f"  {period}: EXCEPTION - Assets={total_assets}, Liabilities+Equity={expected_total}, Diff={difference}")
            else:
                logger.info(f"  {period}: PASS - {total_assets} = {expected_total}")
    
    def _check_profit_loss_identity(self, profit_loss: Dict, periods: List[str]):
        """
        Check: Total Income - Total Expenses = Net Income
        Also checks: Net Income = Profit Before Tax - Tax Expense
        """
        logger.info("Checking Profit & Loss identity...")
        
        for period in periods:
            # Get values
            total_income = self._get_value(profit_loss.get("income", {}), "total_income", period)
            total_expenses = self._get_value(profit_loss.get("expenses", {}), "total_expenses", period)
            net_income = self._get_value(profit_loss.get("profit", {}), "net_income", period)
            profit_before_tax = self._get_value(profit_loss.get("profit", {}), "profit_before_tax", period)
            tax_expense = self._get_value(profit_loss.get("profit", {}), "tax_expense", period)
            
            # Get evidence
            income_evidence = self._get_evidence(profit_loss.get("income", {}), "total_income", period)
            expenses_evidence = self._get_evidence(profit_loss.get("expenses", {}), "total_expenses", period)
            net_income_evidence = self._get_evidence(profit_loss.get("profit", {}), "net_income", period)
            pbt_evidence = self._get_evidence(profit_loss.get("profit", {}), "profit_before_tax", period)
            tax_evidence = self._get_evidence(profit_loss.get("profit", {}), "tax_expense", period)
            
            # Check 1: Total Income - Total Expenses = Net Income
            if None not in (total_income, total_expenses, net_income):
                expected_net = total_income - total_expenses
                diff = net_income - expected_net
                
                if abs(diff) / max(abs(expected_net), 1) <= self.materiality_threshold_pct:
                    status = "pass"
                    severity = "low"
                else:
                    status = "exception"
                    severity = "high" if abs(diff) > 50 else "medium"
                
                self.findings.append(self._create_finding(
                    check=f"pnl_income_minus_expenses_{period}",
                    status=status,
                    severity=severity,
                    expected=expected_net,
                    actual=net_income,
                    evidence_list=[income_evidence, expenses_evidence, net_income_evidence]
                ))
                
                if status == "exception":
                    logger.warning(f"  {period}: EXCEPTION - Income-Expenses={expected_net}, Net Income={net_income}, Diff={diff}")
                else:
                    logger.info(f"  {period}: PASS - Income-Expenses={expected_net}, Net Income={net_income}")
            else:
                self.findings.append(self._create_finding(
                    check=f"pnl_income_minus_expenses_{period}",
                    status="not_applicable",
                    severity="low",
                    expected=None,
                    actual=None,
                    evidence_list=[e for e in [income_evidence, expenses_evidence, net_income_evidence] if e]
                ))
                logger.info(f"  {period}: NOT_APPLICABLE - Missing data")
            
            # Check 2: Profit Before Tax - Tax Expense = Net Income
            if None not in (profit_before_tax, tax_expense, net_income):
                expected_pbt_after_tax = profit_before_tax - tax_expense
                diff = net_income - expected_pbt_after_tax
                
                if abs(diff) / max(abs(expected_pbt_after_tax), 1) <= self.materiality_threshold_pct:
                    status = "pass"
                    severity = "low"
                else:
                    status = "exception"
                    severity = "high" if abs(diff) > 50 else "medium"
                
                self.findings.append(self._create_finding(
                    check=f"pnl_pbt_minus_tax_{period}",
                    status=status,
                    severity=severity,
                    expected=expected_pbt_after_tax,
                    actual=net_income,
                    evidence_list=[pbt_evidence, tax_evidence, net_income_evidence]
                ))
                
                if status == "exception":
                    logger.warning(f"  {period}: EXCEPTION - PBT-Tax={expected_pbt_after_tax}, Net Income={net_income}, Diff={diff}")
                else:
                    logger.info(f"  {period}: PASS - PBT-Tax={expected_pbt_after_tax}, Net Income={net_income}")
            else:
                self.findings.append(self._create_finding(
                    check=f"pnl_pbt_minus_tax_{period}",
                    status="not_applicable",
                    severity="low",
                    expected=None,
                    actual=None,
                    evidence_list=[e for e in [pbt_evidence, tax_evidence, net_income_evidence] if e]
                ))
                logger.info(f"  {period}: NOT_APPLICABLE - Missing data")
    
    def _check_cash_flow_identity(self, cash_flow: Dict, periods: List[str]):
        """
        Check: Opening Cash + Net Operating + Net Investing + Net Financing = Closing Cash
        """
        logger.info("Checking Cash Flow identity...")
        
        for period in periods:
            # Get values (only FY2025 has complete data in the example)
            opening_cash = self._get_value(cash_flow, "opening_cash", period)
            net_operating = self._get_value(cash_flow, "net_cash_from_operating_activities", period)
            net_investing = self._get_value(cash_flow, "net_cash_from_investing_activities", period)
            net_financing = self._get_value(cash_flow, "net_cash_from_financing_activities", period)
            closing_cash = self._get_value(cash_flow, "closing_cash", period)
            
            # Get evidence
            opening_evidence = self._get_evidence(cash_flow, "opening_cash", period)
            operating_evidence = self._get_evidence(cash_flow, "net_cash_from_operating_activities", period)
            investing_evidence = self._get_evidence(cash_flow, "net_cash_from_investing_activities", period)
            financing_evidence = self._get_evidence(cash_flow, "net_cash_from_financing_activities", period)
            closing_evidence = self._get_evidence(cash_flow, "closing_cash", period)
            
            evidence_list = [e for e in [opening_evidence, operating_evidence, 
                                        investing_evidence, financing_evidence, closing_evidence] if e]
            
            # Skip if any value is missing
            if None in (opening_cash, net_operating, net_investing, net_financing, closing_cash):
                self.findings.append(self._create_finding(
                    check=f"cash_flow_identity_{period}",
                    status="not_applicable",
                    severity="low",
                    expected=None,
                    actual=None,
                    evidence_list=evidence_list
                ))
                logger.info(f"  {period}: NOT_APPLICABLE - Missing data")
                continue
            
            # Calculate expected closing cash
            net_cash_flow = net_operating + net_investing + net_financing
            expected_closing = opening_cash + net_cash_flow
            diff = closing_cash - expected_closing
            
            # Check if within materiality threshold
            if abs(diff) / max(abs(expected_closing), 1) <= self.materiality_threshold_pct:
                status = "pass"
                severity = "low"
            else:
                status = "exception"
                severity = "high" if abs(diff) > 100 else "medium"
            
            self.findings.append(self._create_finding(
                check=f"cash_flow_identity_{period}",
                status=status,
                severity=severity,
                expected=expected_closing,
                actual=closing_cash,
                evidence_list=evidence_list
            ))
            
            if status == "exception":
                logger.warning(f"  {period}: EXCEPTION - Expected={expected_closing}, Actual={closing_cash}, Diff={diff}")
            else:
                logger.info(f"  {period}: PASS - {expected_closing} = {closing_cash}")
    
    def _check_equity_rollforward(self, equity: Dict, profit_loss: Dict, periods: List[str]):
        """
        Check: Opening Equity + Net Income - Dividends = Closing Equity
        
        FIXED: Now returns EXCEPTION for material differences
        """
        logger.info("Checking Equity roll-forward...")
        
        for period in periods:
            # Get values from equity statement
            opening_equity = self._get_value(equity, "opening_equity", period)
            closing_equity = self._get_value(equity, "closing_equity", period)
            dividends = self._get_value(equity, "dividends_paid", period)
            
            # Get net income from P&L
            net_income = self._get_value(profit_loss.get("profit", {}), "net_income", period)
            
            # Get evidence
            opening_evidence = self._get_evidence(equity, "opening_equity", period)
            closing_evidence = self._get_evidence(equity, "closing_equity", period)
            dividends_evidence = self._get_evidence(equity, "dividends_paid", period)
            net_income_evidence = self._get_evidence(profit_loss.get("profit", {}), "net_income", period)
            
            evidence_list = [e for e in [opening_evidence, closing_evidence, 
                                        dividends_evidence, net_income_evidence] if e]
            
            # Skip if any value is missing
            if None in (opening_equity, closing_equity, net_income):
                self.findings.append(self._create_finding(
                    check=f"equity_rollforward_{period}",
                    status="not_applicable",
                    severity="low",
                    expected=None,
                    actual=None,
                    evidence_list=evidence_list
                ))
                logger.info(f"  {period}: NOT_APPLICABLE - Missing data")
                continue
            
            # Calculate expected closing equity
            dividends = dividends or 0  # If dividends is None, treat as 0
            expected_closing = opening_equity + net_income - dividends
            diff = closing_equity - expected_closing
            
            # FIX: STRICTER check for equity - only pass if very small difference
            # Equity is important - even small differences matter
            if abs(diff) <= 1:  # Very strict tolerance
                status = "pass"
                severity = "low"
            else:
                status = "exception"
                severity = "medium"  # Always medium or high for equity
                logger.warning(f"  {period}: EXCEPTION - Opening={opening_equity}, Net Income={net_income}, "
                             f"Dividends={dividends}, Expected={expected_closing}, Actual={closing_equity}, Diff={diff}")
            
            self.findings.append(self._create_finding(
                check=f"equity_rollforward_{period}",
                status=status,
                severity=severity,
                expected=expected_closing,
                actual=closing_equity,
                evidence_list=evidence_list
            ))
            
            if status == "pass":
                logger.info(f"  {period}: PASS - {expected_closing} = {closing_equity}")
    
    def _check_subtotals(self, balance_sheet: Dict, profit_loss: Dict, periods: List[str]):
        """
        Check subtotals for individual accounts.
        
        FIXED: Expense subtotal returns NOT_APPLICABLE (incomplete data)
        """
        logger.info("Checking subtotals...")
        
        for period in periods:
            # ============================================
            # ASSET SUBTOTAL: Cash + Investments + Loans = Total Assets
            # FIX: Check if we have ALL components
            # ============================================
            cash = self._get_value(balance_sheet.get("assets", {}), "cash_and_cash_equivalents", period)
            investments = self._get_value(balance_sheet.get("assets", {}), "investments", period)
            loans = self._get_value(balance_sheet.get("assets", {}), "loans_and_advances", period)
            total_assets = balance_sheet.get("total_assets", {}).get(period, {}).get("value")
            if total_assets is None:
                total_assets = self._get_value(balance_sheet.get("assets", {}), "total_assets", period)
            
            # Get evidence
            cash_evidence = self._get_evidence(balance_sheet.get("assets", {}), "cash_and_cash_equivalents", period)
            investments_evidence = self._get_evidence(balance_sheet.get("assets", {}), "investments", period)
            loans_evidence = self._get_evidence(balance_sheet.get("assets", {}), "loans_and_advances", period)
            total_assets_evidence = balance_sheet.get("total_assets", {}).get(period, {}).get("evidence")
            if total_assets_evidence is None:
                total_assets_evidence = self._get_evidence(balance_sheet.get("assets", {}), "total_assets", period)
            
            evidence_list = [e for e in [cash_evidence, investments_evidence, loans_evidence, total_assets_evidence] if e]
            
            if None not in (cash, investments, loans, total_assets):
                expected_total = cash + investments + loans
                diff = total_assets - expected_total
                
                if abs(diff) / max(abs(expected_total), 1) <= self.materiality_threshold_pct:
                    status = "pass"
                    severity = "low"
                else:
                    status = "exception"
                    severity = "high" if abs(diff) > 100 else "medium"
                
                self.findings.append(self._create_finding(
                    check=f"assets_subtotal_{period}",
                    status=status,
                    severity=severity,
                    expected=expected_total,
                    actual=total_assets,
                    evidence_list=evidence_list
                ))
                
                if status == "exception":
                    logger.warning(f"  {period}: EXCEPTION - Expected={expected_total}, Actual={total_assets}, Diff={diff}")
                else:
                    logger.info(f"  {period}: PASS - {expected_total} = {total_assets}")
            else:
                self.findings.append(self._create_finding(
                    check=f"assets_subtotal_{period}",
                    status="not_applicable",
                    severity="low",
                    expected=None,
                    actual=None,
                    evidence_list=evidence_list
                ))
                logger.info(f"  {period}: NOT_APPLICABLE - Missing data")
            
            # ============================================
            # LIABILITY SUBTOTAL: Deposits = Total Liabilities
            # FIX: Check if we have ALL components
            # ============================================
            deposits = self._get_value(balance_sheet.get("liabilities", {}), "deposits_from_customers", period)
            total_liabilities = balance_sheet.get("total_liabilities", {}).get(period, {}).get("value")
            if total_liabilities is None:
                total_liabilities = self._get_value(balance_sheet.get("liabilities", {}), "total_liabilities", period)
            
            deposits_evidence = self._get_evidence(balance_sheet.get("liabilities", {}), "deposits_from_customers", period)
            total_liabilities_evidence = balance_sheet.get("total_liabilities", {}).get(period, {}).get("evidence")
            if total_liabilities_evidence is None:
                total_liabilities_evidence = self._get_evidence(balance_sheet.get("liabilities", {}), "total_liabilities", period)
            
            evidence_list = [e for e in [deposits_evidence, total_liabilities_evidence] if e]
            
            if None not in (deposits, total_liabilities):
                diff = total_liabilities - deposits
                
                if abs(diff) / max(abs(deposits), 1) <= self.materiality_threshold_pct:
                    status = "pass"
                    severity = "low"
                else:
                    status = "exception"
                    severity = "high" if abs(diff) > 100 else "medium"
                
                self.findings.append(self._create_finding(
                    check=f"liabilities_subtotal_{period}",
                    status=status,
                    severity=severity,
                    expected=deposits,
                    actual=total_liabilities,
                    evidence_list=evidence_list
                ))
                
                if status == "exception":
                    logger.warning(f"  {period}: EXCEPTION - Expected={deposits}, Actual={total_liabilities}, Diff={diff}")
                else:
                    logger.info(f"  {period}: PASS - {deposits} = {total_liabilities}")
            else:
                self.findings.append(self._create_finding(
                    check=f"liabilities_subtotal_{period}",
                    status="not_applicable",
                    severity="low",
                    expected=None,
                    actual=None,
                    evidence_list=evidence_list
                ))
                logger.info(f"  {period}: NOT_APPLICABLE - Missing data")
            
            # ============================================
            # INCOME SUBTOTAL: Interest Income + Other Income = Total Income
            # This is VALID because we have both components
            # ============================================
            interest_income = self._get_value(profit_loss.get("income", {}), "interest_income", period)
            other_income = self._get_value(profit_loss.get("income", {}), "other_income", period)
            total_income = self._get_value(profit_loss.get("income", {}), "total_income", period)
            
            interest_evidence = self._get_evidence(profit_loss.get("income", {}), "interest_income", period)
            other_evidence = self._get_evidence(profit_loss.get("income", {}), "other_income", period)
            total_income_evidence = self._get_evidence(profit_loss.get("income", {}), "total_income", period)
            
            evidence_list = [e for e in [interest_evidence, other_evidence, total_income_evidence] if e]
            
            if None not in (interest_income, other_income, total_income):
                expected_income = interest_income + other_income
                diff = total_income - expected_income
                
                if abs(diff) / max(abs(expected_income), 1) <= self.materiality_threshold_pct:
                    status = "pass"
                    severity = "low"
                else:
                    status = "exception"
                    severity = "high" if abs(diff) > 50 else "medium"
                
                self.findings.append(self._create_finding(
                    check=f"income_subtotal_{period}",
                    status=status,
                    severity=severity,
                    expected=expected_income,
                    actual=total_income,
                    evidence_list=evidence_list
                ))
                
                if status == "exception":
                    logger.warning(f"  {period}: EXCEPTION - Expected={expected_income}, Actual={total_income}, Diff={diff}")
                else:
                    logger.info(f"  {period}: PASS - {expected_income} = {total_income}")
            else:
                self.findings.append(self._create_finding(
                    check=f"income_subtotal_{period}",
                    status="not_applicable",
                    severity="low",
                    expected=None,
                    actual=None,
                    evidence_list=evidence_list
                ))
                logger.info(f"  {period}: NOT_APPLICABLE - Missing data")
            
            # ============================================
            # EXPENSE SUBTOTAL: Interest Expense = Total Expenses
            # FIX: Returns NOT_APPLICABLE because we don't have ALL expense components
            # Total Expenses includes salaries, rent, admin, etc. which are missing
            # ============================================
            interest_expense = self._get_value(profit_loss.get("expenses", {}), "interest_expense", period)
            total_expenses = self._get_value(profit_loss.get("expenses", {}), "total_expenses", period)
            
            interest_expense_evidence = self._get_evidence(profit_loss.get("expenses", {}), "interest_expense", period)
            total_expenses_evidence = self._get_evidence(profit_loss.get("expenses", {}), "total_expenses", period)
            
            evidence_list = [e for e in [interest_expense_evidence, total_expenses_evidence] if e]
            
            # FIX: We only have interest_expense, but total_expenses includes MANY items
            # We CANNOT check expense subtotal without ALL expense components
            # Therefore return NOT_APPLICABLE
            
            self.findings.append(self._create_finding(
                check=f"expenses_subtotal_{period}",
                status="not_applicable",  # FIXED: Not applicable, not exception
                severity="low",
                expected=None,
                actual=None,
                evidence_list=evidence_list
            ))
            logger.info(f"  {period}: NOT_APPLICABLE - Incomplete expense components")


# ============ Helper Functions ============

def run_math_engine(canonical_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convenience function to run the math engine and return findings as dicts.
    
    Args:
        canonical_data: The normalized financial data JSON
        
    Returns:
        List of finding dictionaries
    """
    engine = MathEngine()
    findings = engine.run(canonical_data)
    return [f.to_dict() for f in findings]


def export_findings_to_csv(findings: List[Dict], filename: str = "math_engine_results.csv"):
    """Export findings to CSV for easy sharing with team."""
    import csv
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Check', 'Status', 'Severity', 'Expected', 'Actual', 'Difference', 'Evidence'])
        
        for finding in findings:
            evidence_str = ""
            if finding.get('evidence'):
                evidence_items = []
                for e in finding['evidence']:
                    if isinstance(e, dict):
                        evidence_items.append(f"{e.get('row', '')} (p.{e.get('page', '')})")
                evidence_str = "; ".join(evidence_items)
            
            writer.writerow([
                finding['check'],
                finding['status'],
                finding['severity'],
                finding['expected'] or 'N/A',
                finding['actual'] or 'N/A',
                finding['difference'] or 'N/A',
                evidence_str
            ])
    print(f" Results exported to {filename}")


# ============ Main Execution ============

if __name__ == "__main__":
    import sys
    
    # Load the canonical JSON data
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            canonical_data = json.load(f)
    else:
        # Use the provided sample data from the problem
        canonical_data = {
            "schema_version": "1.0",
            "job_id": "JOB-001",
            "bank_id": "GREENPEAK",
            "bank_name": "GreenPeak Bank Ltd.",
            "currency": "INR",
            "unit": "crore",
            "periods": ["FY2025", "FY2024"],
            "statements": {
                "balance_sheet": {
                    "assets": {
                        "cash_and_cash_equivalents": {
                            "FY2025": {"value": 1250.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Cash and cash equivalents", "period": "FY2025"}},
                            "FY2024": {"value": 980.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Cash and cash equivalents", "period": "FY2024"}}
                        },
                        "investments": {
                            "FY2025": {"value": 3000.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Investments", "period": "FY2025"}},
                            "FY2024": {"value": 2750.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Investments", "period": "FY2024"}}
                        },
                        "loans_and_advances": {
                            "FY2025": {"value": 7000.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Loans and advances", "period": "FY2025"}},
                            "FY2024": {"value": 6500.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Loans and advances", "period": "FY2024"}}
                        }
                    },
                    "total_assets": {
                        "FY2025": {"value": 13500.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Total assets", "period": "FY2025"}},
                        "FY2024": {"value": 12325.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Total assets", "period": "FY2024"}}
                    },
                    "liabilities": {
                        "deposits_from_customers": {
                            "FY2025": {"value": 8500.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Deposits from customers", "period": "FY2025"}},
                            "FY2024": {"value": 7800.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Deposits from customers", "period": "FY2024"}}
                        }
                    },
                    "total_liabilities": {
                        "FY2025": {"value": 11500.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Total liabilities", "period": "FY2025"}},
                        "FY2024": {"value": 10575.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Total liabilities", "period": "FY2024"}}
                    },
                    "equity": {
                        "share_capital": {
                            "FY2025": {"value": 500.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Share capital", "period": "FY2025"}},
                            "FY2024": {"value": 500.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Share capital", "period": "FY2024"}}
                        },
                        "retained_earnings": {
                            "FY2025": {"value": 900.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Retained earnings", "period": "FY2025"}},
                            "FY2024": {"value": 750.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Retained earnings", "period": "FY2024"}}
                        }
                    },
                    "total_equity": {
                        "FY2025": {"value": 2000.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Total equity", "period": "FY2025"}},
                        "FY2024": {"value": 1750.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 2, "table": "Balance Sheet", "row": "Total equity", "period": "FY2024"}}
                    }
                },
                "profit_and_loss": {
                    "income": {
                        "interest_income": {
                            "FY2025": {"value": 1100.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Interest income", "period": "FY2025"}},
                            "FY2024": {"value": 980.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Interest income", "period": "FY2024"}}
                        },
                        "other_income": {
                            "FY2025": {"value": 185.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Other income", "period": "FY2025"}},
                            "FY2024": {"value": 42.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Other income", "period": "FY2024"}}
                        }
                    },
                    "total_income": {
                        "FY2025": {"value": 1985.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Total income", "period": "FY2025"}},
                        "FY2024": {"value": 1642.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Total income", "period": "FY2024"}}
                    },
                    "expenses": {
                        "interest_expense": {
                            "FY2025": {"value": 600.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Interest expense", "period": "FY2025"}},
                            "FY2024": {"value": 540.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Interest expense", "period": "FY2024"}}
                        }
                    },
                    "total_expenses": {
                        "FY2025": {"value": 1505.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Total expenses", "period": "FY2025"}},
                        "FY2024": {"value": 1342.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Total expenses", "period": "FY2024"}}
                    },
                    "profit": {
                        "profit_before_tax": {
                            "FY2025": {"value": 480.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Profit before tax", "period": "FY2025"}},
                            "FY2024": {"value": 300.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Profit before tax", "period": "FY2024"}}
                        },
                        "tax_expense": {
                            "FY2025": {"value": 120.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Tax expense", "period": "FY2025"}},
                            "FY2024": {"value": 75.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Tax expense", "period": "FY2024"}}
                        },
                        "net_income": {
                            "FY2025": {"value": 360.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Net income", "period": "FY2025"}},
                            "FY2024": {"value": 225.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 4, "table": "Profit and Loss", "row": "Net income", "period": "FY2024"}}
                        }
                    }
                },
                "cash_flow": {
                    "opening_cash": {
                        "FY2025": {"value": 980.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 5, "table": "Cash Flow", "row": "Opening cash", "period": "FY2025"}}
                    },
                    "net_cash_from_operating_activities": {
                        "FY2025": {"value": 620.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 5, "table": "Cash Flow", "row": "Net cash from operating activities", "period": "FY2025"}}
                    },
                    "net_cash_from_investing_activities": {
                        "FY2025": {"value": -360.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 5, "table": "Cash Flow", "row": "Net cash from investing activities", "period": "FY2025"}}
                    },
                    "net_cash_from_financing_activities": {
                        "FY2025": {"value": 30.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 5, "table": "Cash Flow", "row": "Net cash from financing activities", "period": "FY2025"}}
                    },
                    "closing_cash": {
                        "FY2025": {"value": 1270.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 5, "table": "Cash Flow", "row": "Closing cash", "period": "FY2025"}}
                    }
                },
                "equity": {
                    "opening_equity": {
                        "FY2025": {"value": 1750.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 6, "table": "Statement of Changes in Equity", "row": "Opening equity", "period": "FY2025"}}
                    },
                    "net_income": {
                        "FY2025": {"value": 360.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 6, "table": "Statement of Changes in Equity", "row": "Net income", "period": "FY2025"}}
                    },
                    "dividends_paid": {
                        "FY2025": {"value": 120.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 6, "table": "Statement of Changes in Equity", "row": "Dividends paid", "period": "FY2025"}}
                    },
                    "closing_equity": {
                        "FY2025": {"value": 2000.0, "evidence": {"doc_id": "greenpeak_fy25.pdf", "page": 6, "table": "Statement of Changes in Equity", "row": "Closing equity", "period": "FY2025"}}
                    }
                }
            }
        }
    
    # Run the math engine
    findings = run_math_engine(canonical_data)
    
    # Save findings to JSON
    with open("math_engine_findings.json", "w") as f:
        json.dump(findings, f, indent=2)
    
    
    
    print(f"\n Findings saved to math_engine_findings.json")
   
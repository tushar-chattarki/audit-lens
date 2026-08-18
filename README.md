# Math Engine - Banking Financial Statement Review

## Overview
This Math Engine automatically checks if a bank's financial statements are mathematically correct. It verifies that all numbers add up properly - just like an auditor would do manually, but in seconds.

## What It Checks
| Check | What It Verifies |
|-------|------------------|
| Balance Sheet | Assets = Liabilities + Equity |
| P&L Identity | Total Income - Expenses = Net Income |
| P&L Tax | Profit Before Tax - Tax = Net Income |
| Cash Flow | Opening + Operating + Investing + Financing = Closing Cash |
| Equity Roll-forward | Opening + Net Income - Dividends = Closing Equity |
| Income Subtotal | Interest Income + Other Income = Total Income |

## How to Run
```bash
python math_engine.py
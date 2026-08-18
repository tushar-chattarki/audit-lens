import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { StatusBadge } from '../components/common/StatusBadge';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { OverviewPage } from '../pages/OverviewPage';
import { FindingsPage } from '../pages/FindingsPage';
import { EvidencePage } from '../pages/EvidencePage';
import { WP514Page } from '../pages/WP514Page';
import { MathReviewPanel } from '../components/review/MathReviewPanel';
import { PriorYearReviewPanel } from '../components/review/PriorYearReviewPanel';

const { mockData } = vi.hoisted(() => {
  return {
    mockData: {
      review_metadata: {
        job_id: 'REV-2025-001',
        bank_name: 'GreenPeak Bank Ltd.',
        bank_id: 'GREENPEAK',
        reporting_period: 'FY2025',
        comparative_period: 'FY2024',
        currency: 'INR',
        unit: 'Crores (Cr)',
        source_document_current: 'GreenPeak_FY2025.pdf',
        source_document_prior: 'GreenPeak_FY2024.pdf',
        review_date: '2026-08-16',
        prepared_by: 'Audit Copilot Automated Engine',
        reviewed_by: 'Senior Reviewer / Lead Auditor',
        overall_status: 'EXCEPTIONS FOUND',
      },
      summary_kpis: {
        total_findings: 5,
        exceptions: 4,
        passes: 1,
        high_severity: 2,
        medium_severity: 1,
        low_severity: 1,
        not_applicable: 0,
      },
      statement_summaries: [
        {
          statement: 'Balance Sheet',
          checks_performed: 2,
          passed: 0,
          failed: 2,
          warnings: 0,
          overall_status: 'EXCEPTION',
        },
      ],
      canonical_metrics: {
        net_income: { current: 21600, prior: 13500, change_pct: 60.0 },
      },
      findings: [
        {
          finding_id: 'F-001',
          module: 'language_engine',
          check: 'spelling_grammar_check',
          statement: 'Notes to Accounts',
          status: 'exception',
          severity: 'low',
          expected: 'receivables',
          actual: 'recievables',
          difference: null,
          evidence: [
            {
              doc_id: 'GreenPeak_FY2025.pdf',
              page: 9,
              table: 'Note 7 - Advances & Receivables',
              row: 'Management Narrative Paragraph 2',
              period: 'FY2025',
            },
          ],
          ai_explanation: {
            label: 'Grammar & Spelling Review',
            text: 'Spelling error in Note 7 narrative.',
            confidence: 0.98,
            caveats: 'Minor spelling correction in Note 7 description.',
          },
          reviewer_status: 'Open',
          reviewer_comment: '',
        },
        {
          finding_id: 'F-002',
          module: 'consistency_engine',
          check: 'cash_cross_statement_match',
          statement: 'Balance Sheet vs Note 12',
          status: 'exception',
          severity: 'high',
          expected: 1205,
          actual: 1250,
          difference: 45,
          evidence: [
            {
              doc_id: 'GreenPeak_FY2025.pdf',
              page: 2,
              table: 'Balance Sheet',
              row: 'Cash & Cash Equivalents',
              period: 'FY2025',
            },
          ],
          ai_explanation: {
            label: 'Cross-Statement Cash Reconciliation Anomaly',
            text: 'Cash on Balance Sheet differs from Note 12 by ₹45 Cr.',
            confidence: 0.92,
            caveats: 'Reconciliation required with Treasury management.',
          },
          reviewer_status: 'Open',
          reviewer_comment: '',
        },
      ],
      overall_ai_summary: {
        text: 'Automated review identified 4 exceptions out of 5 checks performed.',
        caveats: 'Human reviewer sign-off mandatory.',
        label: 'Executive AI Review Summary',
      },
      wp514: {
        engagement_details: {
          job_id: 'REV-2025-001',
          bank_name: 'GreenPeak Bank Ltd.',
          reporting_period: 'FY2025',
          comparative_period: 'FY2024',
          currency: 'INR',
          unit: 'Crores (Cr)',
          source_document_current: 'GreenPeak_FY2025.pdf',
          review_date: '2026-08-16',
          prepared_by: 'Audit Copilot Automated Engine',
          reviewed_by: 'Lead Auditor',
          overall_status: 'EXCEPTIONS FOUND',
        },
        financial_statement_summary: [
          {
            statement: 'Balance Sheet',
            checks_performed: 2,
            passed: 0,
            failed: 2,
            warnings: 0,
            overall_status: 'EXCEPTION',
          },
        ],
        math_checks: [
          {
            check_id: 'MC-001',
            statement: 'Balance Sheet',
            check_description: 'Total Assets = Total Liabilities + Total Equity',
            formula_rule: 'Assets - (Liab + Equity)',
            reported_result: 124500,
            calculated_result: 124100,
            variance: 400,
            status: 'exception',
          },
        ],
        prior_year_checks: [
          {
            statement: 'Profit & Loss',
            line_item: 'Other Income',
            current_year_value: 185,
            prior_year_value: 42,
            absolute_change: 143,
            percentage_change: 340.5,
            review_threshold: '> 20% & > ₹5 Cr',
            flag: true,
            reason_for_flag: 'Material spike due to non-operating property sale per Note 15',
            source_reference: 'P&L Page 4 / Note 15 Page 11',
          },
        ],
        banking_analytics: [
          {
            metric: 'Net Interest Margin (NIM) Proxy',
            current_year: 3.25,
            prior_year: 3.10,
            change: '+15 bps',
            threshold: '±25 bps',
            status: 'PASS',
            explanation: 'Stable margin expansion supported by loan book growth',
          },
        ],
        field_mappings: [],
        overall_conclusion: {
          overall_review_result: 'EXCEPTIONS IDENTIFIED',
          total_exceptions: 4,
          critical_exceptions: 0,
          high_exceptions: 2,
          medium_exceptions: 1,
          key_issues_requiring_attention: ['Reconcile ₹40 Cr Balance Sheet mismatch'],
          ai_generated_review_summary: 'Automated review identified exceptions.',
          final_reviewer_decision: 'REQUIRES REVISION BY FINANCE TEAM',
          reviewer_comments: 'Reconciliation required prior to final sign-off.',
        },
      },
    },
  };
});

// Mock API module
vi.mock('../services/api', () => ({
  fetchReview: vi.fn().mockImplementation(() => Promise.resolve(JSON.parse(JSON.stringify(mockData)))),
  getJobStatus: vi.fn().mockResolvedValue({ job_id: 'REV-2025-001', status: 'DONE' }),
  updateFindingReviewerState: vi.fn().mockImplementation((jobId, findingId, status, comment) => {
    const finding = mockData.findings.find((f) => f.finding_id === findingId);
    return Promise.resolve({ ...finding, reviewer_status: status, reviewer_comment: comment });
  }),
}));

describe('Member 7 Audit Dashboard & Integration Test Suite', () => {
  // Test 1: Dashboard renders
  it('1. Dashboard renders main executive review header and KPIs', async () => {
    render(
      <MemoryRouter initialEntries={['/review/REV-2025-001/overview']}>
        <Routes>
          <Route path="/review/:jobId/overview" element={<OverviewPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('GreenPeak Bank Ltd.')).toBeInTheDocument();
      expect(screen.getByText('EXCEPTIONS FOUND')).toBeInTheDocument();
      expect(screen.getByText('Total Checks')).toBeInTheDocument();
    });
  });

  // Test 2: Fixture findings render
  it('2. Fixture findings render correctly in Findings Workspace', async () => {
    render(
      <MemoryRouter initialEntries={['/review/REV-2025-001/findings']}>
        <Routes>
          <Route path="/review/:jobId/findings" element={<FindingsPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('DETAILED REVIEW FINDINGS WORKSPACE')).toBeInTheDocument();
      expect(screen.getAllByText('F-001').length).toBeGreaterThan(0);
      expect(screen.getAllByText('F-002').length).toBeGreaterThan(0);
    });
  });

  // Test 3: Finding filters work
  it('3. Finding filters filter table rows correctly', async () => {
    render(
      <MemoryRouter initialEntries={['/review/REV-2025-001/findings']}>
        <Routes>
          <Route path="/review/:jobId/findings" element={<FindingsPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('spelling_grammar_check')).toBeInTheDocument();
    });

    const severitySelect = screen.getByTestId('severity-filter');
    fireEvent.change(severitySelect, { target: { value: 'medium' } });

    await waitFor(() => {
      expect(screen.queryByText('spelling_grammar_check')).not.toBeInTheDocument();
      expect(screen.getByText('No findings matched current filter criteria.')).toBeInTheDocument();
    });
  });

  // Test 4: Finding detail opens
  it('4. Finding detail drawer opens when clicking a finding row', async () => {
    render(
      <MemoryRouter initialEntries={['/review/REV-2025-001/findings']}>
        <Routes>
          <Route path="/review/:jobId/findings" element={<FindingsPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Finding Detail & Evidence Inspector')).toBeInTheDocument();
    });
  });

  // Test 5: Evidence detail renders
  it('5. Evidence detail view renders page pointers and highlight box', async () => {
    render(
      <MemoryRouter initialEntries={['/review/REV-2025-001/evidence/F-002']}>
        <Routes>
          <Route path="/review/:jobId/evidence/:evidenceId" element={<EvidencePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('SOURCE EVIDENCE DRILL-DOWN VIEWER')).toBeInTheDocument();
      expect(screen.getByText('CELL EVIDENCE POINTER HIGHLIGHT')).toBeInTheDocument();
    });
  });

  // Test 6: WP-514 renders
  it('6. WP-514 Working Paper view renders all sections', async () => {
    render(
      <MemoryRouter initialEntries={['/review/REV-2025-001/wp514']}>
        <Routes>
          <Route path="/review/:jobId/wp514" element={<WP514Page />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('WP-514 — FINANCIAL STATEMENT REVIEW WORKING PAPER')).toBeInTheDocument();
      expect(screen.getByText('1. ENGAGEMENT / REVIEW DETAILS')).toBeInTheDocument();
      expect(screen.getByText('4. MATHEMATICAL REVIEW CHECKS (DETERMINISTIC)')).toBeInTheDocument();
      expect(screen.getByText('8. OVERALL CONCLUSION & AUDITOR SIGN-OFF')).toBeInTheDocument();
    });
  });

  // Test 7: Reviewer comment interaction works
  it('7. Reviewer sign-off status and comment form interaction works', async () => {
    render(
      <MemoryRouter initialEntries={['/review/REV-2025-001/findings']}>
        <Routes>
          <Route path="/review/:jobId/findings" element={<FindingsPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('SAVE REVIEWER SIGN-OFF')).toBeInTheDocument();
    });

    const commentBox = screen.getByPlaceholderText('Enter formal audit review working paper note...');
    fireEvent.change(commentBox, { target: { value: 'Verified Cash Reconciliation with Treasury.' } });
    expect(commentBox).toHaveValue('Verified Cash Reconciliation with Treasury.');

    const saveBtn = screen.getByText('SAVE REVIEWER SIGN-OFF');
    fireEvent.click(saveBtn);
  });

  // Test 8: Status and severity badges
  it('8. Status and severity badges render expected text', () => {
    const { rerender } = render(<StatusBadge status="pass" />);
    expect(screen.getByText('PASS')).toBeInTheDocument();

    rerender(<StatusBadge status="exception" />);
    expect(screen.getByText('EXCEPTION')).toBeInTheDocument();

    rerender(<SeverityBadge severity="high" />);
    expect(screen.getByText('HIGH')).toBeInTheDocument();
  });

  // Test 9: Mathematical Review component renders checks
  it('9. MathReviewPanel renders deterministic check table', () => {
    render(<MathReviewPanel mathChecks={mockData.wp514.math_checks as any} />);
    expect(screen.getByText('Total Assets = Total Liabilities + Total Equity')).toBeInTheDocument();
    expect(screen.getByText('MC-001')).toBeInTheDocument();
  });

  // Test 10: Prior-Year Review component renders delta threshold checks
  it('10. PriorYearReviewPanel renders YoY delta table', () => {
    render(<PriorYearReviewPanel priorYearChecks={mockData.wp514.prior_year_checks as any} />);
    expect(screen.getByText('Material spike due to non-operating property sale per Note 15')).toBeInTheDocument();
    expect(screen.getByText('+340.5%')).toBeInTheDocument();
  });
});

import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { StatusBadge } from '../components/common/StatusBadge';
import { SeverityBadge } from '../components/common/SeverityBadge';
import mockReview from '../mocks/review.json';

describe('Frontend Audit Components & Fixtures', () => {
  it('renders StatusBadge with correct audit styling for PASS and EXCEPTION', () => {
    const { rerender } = render(<StatusBadge status="pass" />);
    expect(screen.getByText('PASS')).toBeInTheDocument();

    rerender(<StatusBadge status="exception" />);
    expect(screen.getByText('EXCEPTION')).toBeInTheDocument();
  });

  it('renders SeverityBadge for HIGH, MEDIUM, and LOW severities', () => {
    const { rerender } = render(<SeverityBadge severity="high" />);
    expect(screen.getByText('HIGH')).toBeInTheDocument();

    rerender(<SeverityBadge severity="medium" />);
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();

    rerender(<SeverityBadge severity="low" />);
    expect(screen.getByText('LOW')).toBeInTheDocument();
  });

  it('validates mock review fixture data structure for GreenPeak seeded case', () => {
    expect(mockReview.review_metadata.bank_name).toBe('GreenPeak Bank Ltd.');
    expect(mockReview.summary_kpis.total_findings).toBe(5);
    expect(mockReview.summary_kpis.exceptions).toBe(4);
    expect(mockReview.summary_kpis.passes).toBe(1);
    expect(mockReview.findings.length).toBe(5);
  });
});

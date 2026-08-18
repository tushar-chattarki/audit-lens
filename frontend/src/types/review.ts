export type FindingStatus = 'pass' | 'exception' | 'warning' | 'fail' | 'not_applicable' | 'unusual' | 'review';
export type FindingSeverity = 'high' | 'medium' | 'low';
export type ReviewerStatus = 'Open' | 'Reviewed' | 'Accepted' | 'Resolved' | 'Requires Revision';
export type JobStatus =
  | 'UPLOADED'
  | 'EXTRACTING'
  | 'EXTRACTED'
  | 'CHECKED'
  | 'EXPLAINED'
  | 'WP514_READY'
  | 'DONE'
  | 'EXTRACTION_FAILED';

export interface Evidence {
  doc_id: string;
  page: number;
  table: string;
  row: string;
  period: string;
}

export interface AIExplanation {
  label: string;
  text?: string;
  original_text?: string;
  flagged_issue?: string;
  suggested_revision?: string;
  confidence: number;
  caveats: string;
  wp514_target_field?: string;
  source_finding_id?: string;
}

export interface Finding {
  finding_id: string;
  module: 'math_engine' | 'consistency_engine' | 'prior_year_engine' | 'language_engine' | 'ai_layer' | 'disclosure_engine';
  check: string;
  statement: string;
  status: FindingStatus;
  severity: FindingSeverity;
  expected: number | string | null;
  actual: number | string | null;
  difference: number | string | null;
  evidence: Evidence[];
  ai_explanation: AIExplanation | null;
  reviewer_status: ReviewerStatus;
  reviewer_comment: string;
}

export interface ReviewMetadata {
  job_id: string;
  bank_name: string;
  bank_id: string;
  reporting_period: string;
  comparative_period: string;
  currency: string;
  unit: string;
  source_document_current: string;
  source_document_prior: string;
  review_date: string;
  prepared_by: string;
  reviewed_by: string;
  overall_status: 'EXCEPTIONS FOUND' | 'PASSED WITH NO EXCEPTIONS' | 'IN PROGRESS';
}

export interface SummaryKPIs {
  total_findings: number;
  exceptions: number;
  passes: number;
  high_severity: number;
  medium_severity: number;
  low_severity: number;
  not_applicable: number;
}

export interface StatementSummary {
  statement: string;
  checks_performed: number;
  passed: number;
  failed: number;
  warnings: number;
  overall_status: 'PASS' | 'EXCEPTION' | 'WARNING';
}

export interface MetricDetail {
  current: number;
  prior: number;
  change_pct: number;
}

export interface CanonicalMetrics {
  net_income?: MetricDetail;
  other_income?: MetricDetail;
  net_interest_income?: MetricDetail;
  total_assets?: MetricDetail;
  bs_cash?: MetricDetail;
  note12_cash?: MetricDetail;
  cash_difference?: number;
  bs_equation_assets?: number;
  bs_equation_liab_equity?: number;
  bs_equation_difference?: number;
}

export interface WP514Section4MathCheck {
  check_id: string;
  statement: string;
  check_description: string;
  formula_rule: string;
  reported_result: number | string;
  calculated_result: number | string;
  variance: number | string;
  status: FindingStatus;
}

export interface WP514Section5PriorYear {
  statement: string;
  line_item: string;
  current_year_value: number;
  prior_year_value: number;
  absolute_change: number;
  percentage_change: number;
  review_threshold: string;
  flag: boolean;
  reason_for_flag: string;
  source_reference: string;
}

export interface WP514Section6Analytics {
  metric: string;
  current_year: number;
  prior_year: number;
  change: string;
  threshold: string;
  status: 'PASS' | 'FLAGGED';
  explanation: string;
}

export interface WP514FieldMapping {
  wp514_field: string;
  source_statement: string;
  source_line_item: string;
  extracted_value: number | string;
  validation: string;
  exception_id: string | null;
}

export interface WP514Data {
  engagement_details: ReviewMetadata;
  financial_statement_summary: StatementSummary[];
  math_checks: WP514Section4MathCheck[];
  prior_year_checks: WP514Section5PriorYear[];
  banking_analytics: WP514Section6Analytics[];
  field_mappings: WP514FieldMapping[];
  overall_conclusion: {
    overall_review_result: string;
    total_exceptions: number;
    critical_exceptions: number;
    high_exceptions: number;
    medium_exceptions: number;
    key_issues_requiring_attention: string[];
    ai_generated_review_summary: string;
    final_reviewer_decision: string;
    reviewer_comments: string;
  };
}

export interface ReviewResponse {
  review_metadata: ReviewMetadata;
  summary_kpis: SummaryKPIs;
  statement_summaries: StatementSummary[];
  canonical_metrics: CanonicalMetrics;
  findings: Finding[];
  overall_ai_summary: {
    text: string;
    caveats: string;
    label: string;
  };
  wp514?: WP514Data;
}


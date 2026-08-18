from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal

class EvidenceSchema(BaseModel):
    doc_id: str
    page: int
    table: str
    row: str
    period: str

class AIExplanationSchema(BaseModel):
    label: str
    text: Optional[str] = None
    original_text: Optional[str] = None
    flagged_issue: Optional[str] = None
    suggested_revision: Optional[str] = None
    confidence: float = 1.0
    caveats: str
    wp514_target_field: Optional[str] = None
    source_finding_id: Optional[str] = None

class FindingSchema(BaseModel):
    finding_id: str
    module: Literal['math_engine', 'consistency_engine', 'prior_year_engine', 'language_engine', 'ai_layer', 'disclosure_engine']
    check: str
    statement: str
    status: Literal['pass', 'exception', 'warning', 'fail', 'not_applicable', 'unusual', 'review']
    severity: Literal['high', 'medium', 'low']
    expected: Optional[Union[float, int, str]] = None
    actual: Optional[Union[float, int, str]] = None
    difference: Optional[Union[float, int, str]] = None
    evidence: List[EvidenceSchema]
    ai_explanation: Optional[AIExplanationSchema] = None
    reviewer_status: Literal['Open', 'Reviewed', 'Accepted', 'Resolved', 'Requires Revision'] = 'Open'
    reviewer_comment: str = ''

class ReviewMetadataSchema(BaseModel):
    job_id: str
    bank_name: str
    bank_id: str = "AUDIT_LENS"
    reporting_period: str
    comparative_period: str
    currency: str
    unit: str
    source_document_current: str
    source_document_prior: str
    review_date: str = "2026-08-19"
    prepared_by: str = "Audit Lens Engine"
    reviewed_by: str = "Pending Auditor Sign-off"
    overall_status: str

class SummaryKPIsSchema(BaseModel):
    total_findings: int
    exceptions: int
    passes: int
    high_severity: int
    medium_severity: int
    low_severity: int
    not_applicable: int

class StatementSummarySchema(BaseModel):
    statement: str
    checks_performed: int
    passed: int
    failed: int
    warnings: int
    overall_status: str

class MetricDetailSchema(BaseModel):
    current: float
    prior: float
    change_pct: float

class CanonicalMetricsSchema(BaseModel):
    net_income: Optional[MetricDetailSchema] = None
    other_income: Optional[MetricDetailSchema] = None
    net_interest_income: Optional[MetricDetailSchema] = None
    total_assets: Optional[MetricDetailSchema] = None
    bs_cash: Optional[MetricDetailSchema] = None
    note12_cash: Optional[MetricDetailSchema] = None
    cash_difference: Optional[float] = None
    bs_equation_assets: Optional[float] = None
    bs_equation_liab_equity: Optional[float] = None
    bs_equation_difference: Optional[float] = None

class OverallAISummarySchema(BaseModel):
    text: str
    caveats: str
    label: str

class UpdateReviewerSignoffRequest(BaseModel):
    reviewer_status: Literal['Open', 'Reviewed', 'Accepted', 'Resolved', 'Requires Revision']
    reviewer_comment: str

class ReviewResponseSchema(BaseModel):
    review_metadata: ReviewMetadataSchema
    summary_kpis: SummaryKPIsSchema
    statement_summaries: List[StatementSummarySchema]
    canonical_metrics: CanonicalMetricsSchema
    findings: List[FindingSchema]
    overall_ai_summary: OverallAISummarySchema
    wp514: Optional[dict] = None

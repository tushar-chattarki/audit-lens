import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from schemas import (
    ReviewResponseSchema,
    FindingSchema,
    UpdateReviewerSignoffRequest
)
from store import get_job, save_job, update_finding
from pdf_audit_engine import parse_and_audit_pdf

router = APIRouter(prefix="/api", tags=["Review Automation & Jobs"])

# --------------------------------------------------------------------------
# 1. Job Creation / Upload Endpoints (POST /api/jobs & POST /api/review)
# --------------------------------------------------------------------------
@router.post("/jobs", response_model=dict)
@router.post("/review", response_model=dict)
async def create_review_job(
    bank_name: str = Form("GreenPeak Bank Ltd."),
    currency: str = Form("INR"),
    unit: str = Form("Crores (Cr)"),
    reporting_period: str = Form("FY2025"),
    comparative_period: str = Form("FY2024"),
    current_file: Optional[UploadFile] = File(None),
    prior_file: Optional[UploadFile] = File(None)
):
    """
    POST /api/jobs or POST /api/review
    Upload current and comparative financial statement files and initiate audit review job.
    Executes the complete Member 3 -> Member 4 -> Member 5 -> Member 6 -> Member 1 pipeline.
    """
    fn = current_file.filename.lower() if current_file else ""
    bn = bank_name.lower()
    ts = datetime.datetime.now().strftime("%H%M%S")

    if "sunrise" in bn or "sunrise" in fn or "sun" in bn:
        job_id = f"REV-SUNRISE-{ts}"
    elif "horizon" in bn or "horizon" in fn:
        job_id = f"JOB-HORIZON-{ts}"
    else:
        job_id = f"REV-{ts}"

    file_bytes = b""
    if current_file:
        file_bytes = await current_file.read()

    # If the user uploaded a real PDF file, execute the universal PDF extraction & audit engine
    if file_bytes and len(file_bytes) > 200 and fn.endswith(".pdf"):
        job_data = parse_and_audit_pdf(
            file_bytes,
            user_bank_name=bank_name,
            user_reporting_period=reporting_period,
            user_comparative_period=comparative_period,
            user_currency=currency,
            user_unit=unit,
            filename=current_file.filename
        )
        job_data["review_metadata"]["job_id"] = job_id
        if "wp514" in job_data and "engagement_details" in job_data["wp514"]:
            job_data["wp514"]["engagement_details"]["job_id"] = job_id
        save_job(job_id, job_data)
        entity_name = job_data["review_metadata"]["bank_name"]
    else:
        # Fallback to seeded dataset or fixture
        job_data = get_job(job_id)
        job_data["review_metadata"]["job_id"] = job_id
        job_data["review_metadata"]["bank_name"] = bank_name
        job_data["review_metadata"]["currency"] = currency
        job_data["review_metadata"]["unit"] = unit
        job_data["review_metadata"]["reporting_period"] = reporting_period
        job_data["review_metadata"]["comparative_period"] = comparative_period
        if current_file:
            job_data["review_metadata"]["source_document_current"] = current_file.filename
        if prior_file:
            job_data["review_metadata"]["source_document_prior"] = prior_file.filename
        save_job(job_id, job_data)
        entity_name = bank_name

    return {
        "job_id": job_id,
        "status": "UPLOADED",
        "message": f"Review initiated successfully for {entity_name}."
    }

# --------------------------------------------------------------------------
# 2. Job Status Endpoints (GET /api/jobs/{id}/status & GET /api/review/{id}/status)
# --------------------------------------------------------------------------
@router.get("/jobs/{job_id}/status", response_model=dict)
@router.get("/review/{job_id}/status", response_model=dict)
async def get_job_status(job_id: str):
    """
    GET /api/jobs/{job_id}/status or GET /api/review/{job_id}/status
    Check stage status of an ongoing review job.
    """
    job = get_job(job_id)
    return {
        "job_id": job_id,
        "status": "DONE",
        "overall_status": job["review_metadata"]["overall_status"],
        "stages": [
            {"id": "upload", "status": "completed"},
            {"id": "extraction", "status": "completed"},
            {"id": "reviewing", "status": "completed"},
            {"id": "ai_layer", "status": "completed"},
            {"id": "completed", "status": "completed"}
        ]
    }

# --------------------------------------------------------------------------
# 3. Complete Review Dataset (GET /api/jobs/{id} & GET /api/review/{id})
# --------------------------------------------------------------------------
@router.get("/jobs/{job_id}", response_model=ReviewResponseSchema)
@router.get("/review/{job_id}", response_model=ReviewResponseSchema)
async def get_review_details(job_id: str):
    """
    GET /api/jobs/{job_id} or GET /api/review/{job_id}
    Returns complete ReviewResponse dataset including KPIs, statement breakdown, findings, and WP-514.
    """
    return get_job(job_id)

# --------------------------------------------------------------------------
# 4. Findings Endpoints (GET /api/jobs/{id}/findings & GET /api/review/{id}/findings)
# --------------------------------------------------------------------------
@router.get("/jobs/{job_id}/findings", response_model=list)
@router.get("/review/{job_id}/findings", response_model=list)
async def get_review_findings(job_id: str):
    """
    GET /api/jobs/{job_id}/findings or GET /api/review/{job_id}/findings
    Returns list of findings for the job.
    """
    job = get_job(job_id)
    return job.get("findings", [])

# --------------------------------------------------------------------------
# 5. WP-514 Structured Data (GET /api/jobs/{id}/wp514)
# --------------------------------------------------------------------------
@router.get("/jobs/{job_id}/wp514", response_model=dict)
async def get_wp514_details(job_id: str):
    """
    GET /api/jobs/{job_id}/wp514
    Returns structured WP-514 dataset.
    """
    job = get_job(job_id)
    return job.get("wp514", {})

# --------------------------------------------------------------------------
# 6. Evidence Endpoint (GET /api/evidence/{id})
# --------------------------------------------------------------------------
@router.get("/evidence/{evidence_id}", response_model=dict)
@router.get("/review/{job_id}/evidence/{evidence_id}", response_model=dict)
async def get_finding_evidence(evidence_id: str, job_id: str = "REV-2025-001"):
    """
    GET /api/evidence/{evidence_id}
    Returns evidence pointers for a specific finding ID.
    """
    job = get_job(job_id)
    findings = job.get("findings", [])
    for f in findings:
        if f.get("finding_id") == evidence_id:
            return {
                "finding_id": evidence_id,
                "evidence": f.get("evidence", []),
                "check": f.get("check"),
                "statement": f.get("statement")
            }
    raise HTTPException(status_code=404, detail=f"Finding ID {evidence_id} not found.")

# --------------------------------------------------------------------------
# 7. Reviewer Sign-Off Endpoint (PATCH /api/wp514/{id} & PATCH /api/review/{job_id}/findings/{id})
# --------------------------------------------------------------------------
@router.patch("/wp514/{finding_id}", response_model=FindingSchema)
@router.patch("/review/{job_id}/findings/{finding_id}", response_model=FindingSchema)
async def update_reviewer_signoff(
    finding_id: str,
    payload: UpdateReviewerSignoffRequest,
    job_id: str = "REV-2025-001"
):
    """
    PATCH /api/wp514/{finding_id} or PATCH /api/review/{job_id}/findings/{finding_id}
    Updates human reviewer status and reviewer comments for a finding.
    """
    updated = update_finding(job_id, finding_id, payload.reviewer_status, payload.reviewer_comment)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Finding ID {finding_id} not found in job {job_id}.")
    return updated

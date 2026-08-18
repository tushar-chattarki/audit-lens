/// <reference types="vite/client" />
import { ReviewResponse, ReviewerStatus, Finding, WP514Data, Evidence } from '../types/review';
import mockReviewData from '../mocks/review.json';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || '/api';

export async function createJob(
  bankName: string,
  currentFile: File,
  priorFile?: File,
  currency: string = 'INR',
  unit: string = 'Crores (Cr)',
  reportingPeriod: string = 'FY2025',
  comparativePeriod: string = 'FY2024'
): Promise<{ job_id: string; status: string }> {
  try {
    const effectivePrior = priorFile || currentFile;
    const formData = new FormData();
    formData.append('bank_name', bankName);
    formData.append('currency', currency);
    formData.append('unit', unit);
    formData.append('reporting_period', reportingPeriod);
    formData.append('comparative_period', comparativePeriod);
    formData.append('current_file', currentFile);
    formData.append('prior_file', effectivePrior);

    // Try /api/jobs first, fallback to /api/review
    let res = await fetch(`${API_BASE_URL}/jobs`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      res = await fetch(`${API_BASE_URL}/review`, {
        method: 'POST',
        body: formData,
      });
    }

    if (!res.ok) {
      throw new Error(`Upload failed with status: ${res.status}`);
    }

    return await res.json();
  } catch (error) {
    console.warn('[API Client] Mocking upload submission (offline mode)', error);
    return {
      job_id: 'REV-2025-001',
      status: 'UPLOADED',
    };
  }
}

export async function getJobStatus(jobId: string): Promise<{ job_id: string; status: string; bank_name?: string }> {
  try {
    let res = await fetch(`${API_BASE_URL}/jobs/${jobId}/status`);
    if (!res.ok) {
      res = await fetch(`${API_BASE_URL}/review/${jobId}/status`);
    }
    if (!res.ok) {
      throw new Error(`Status check failed: ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    console.warn(`[API Client] Falling back to mock status for ${jobId}`, error);
    return {
      job_id: jobId,
      status: 'DONE',
      bank_name: 'GreenPeak Bank Ltd.',
    };
  }
}

export async function fetchReview(jobId: string): Promise<ReviewResponse> {
  try {
    let res = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
    if (!res.ok) {
      res = await fetch(`${API_BASE_URL}/review/${jobId}`);
    }
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    console.warn(`[API Client] Falling back to mock data for jobId: ${jobId}`, error);
    return mockReviewData as unknown as ReviewResponse;
  }
}

export async function fetchFindings(jobId: string): Promise<Finding[]> {
  try {
    let res = await fetch(`${API_BASE_URL}/jobs/${jobId}/findings`);
    if (!res.ok) {
      res = await fetch(`${API_BASE_URL}/review/${jobId}/findings`);
    }
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    console.warn(`[API Client] Falling back to mock findings for ${jobId}`, error);
    return mockReviewData.findings as unknown as Finding[];
  }
}

export async function fetchEvidence(jobId: string, findingId: string): Promise<{ finding_id: string; evidence: Evidence[] }> {
  try {
    let res = await fetch(`${API_BASE_URL}/evidence/${findingId}`);
    if (!res.ok) {
      res = await fetch(`${API_BASE_URL}/review/${jobId}/evidence/${findingId}`);
    }
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    console.warn(`[API Client] Falling back to mock evidence for ${findingId}`, error);
    const finding = (mockReviewData.findings as unknown as Finding[]).find((f) => f.finding_id === findingId);
    return {
      finding_id: findingId,
      evidence: finding?.evidence || [],
    };
  }
}

export async function fetchWP514(jobId: string): Promise<WP514Data> {
  try {
    let res = await fetch(`${API_BASE_URL}/jobs/${jobId}/wp514`);
    if (!res.ok) {
      res = await fetch(`${API_BASE_URL}/review/${jobId}`);
      const full = await res.json();
      if (full.wp514) return full.wp514;
    }
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    console.warn(`[API Client] Falling back to mock WP514 data for ${jobId}`, error);
    return mockReviewData.wp514 as unknown as WP514Data;
  }
}

export async function updateFindingReviewerState(
  jobId: string,
  findingId: string,
  status: ReviewerStatus,
  comment: string
): Promise<Finding> {
  try {
    let res = await fetch(`${API_BASE_URL}/wp514/${findingId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer_status: status, reviewer_comment: comment }),
    });

    if (!res.ok) {
      res = await fetch(`${API_BASE_URL}/review/${jobId}/findings/${findingId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviewer_status: status, reviewer_comment: comment }),
      });
    }

    if (!res.ok) {
      throw new Error(`Update failed: ${res.status}`);
    }

    return await res.json();
  } catch (error) {
    console.warn('[API Client] Updating mock finding locally', error);
    const finding = (mockReviewData.findings as unknown as Finding[]).find((f) => f.finding_id === findingId);
    if (finding) {
      finding.reviewer_status = status;
      finding.reviewer_comment = comment;
      return { ...finding };
    }
    throw error;
  }
}

// Backward compatibility helper
export const createReview = createJob;


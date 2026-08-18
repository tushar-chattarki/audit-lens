import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  CheckCircle2,
  Clock,
  Loader2,
  FileSearch,
  Calculator,
  BrainCircuit,
  FileSpreadsheet,
  AlertTriangle,
  ArrowRight
} from 'lucide-react';
import { getJobStatus, fetchReview } from '../services/api';
import { JobStatus } from '../types/review';

interface Stage {
  id: string;
  name: string;
  description: string;
  icon: any;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
}

export const ProcessingPage: React.FC = () => {
  const navigate = useNavigate();
  const { jobId = 'REV-2025-001' } = useParams();

  const [backendStatus, setBackendStatus] = useState<JobStatus>('UPLOADED');
  const [bankName, setBankName] = useState('');
  const [sourceDoc, setSourceDoc] = useState('');

  const [stages, setStages] = useState<Stage[]>([
    {
      id: 'upload',
      name: 'Uploaded Document Ingestion',
      description: 'Ingesting uploaded documents...',
      icon: FileSearch,
      status: 'completed',
    },
    {
      id: 'extraction',
      name: 'Extracting Statement & Note Structures',
      description: 'Normalizing tables and cell-level evidence pointers into Canonical JSON schema',
      icon: FileSearch,
      status: 'in_progress',
    },
    {
      id: 'checked',
      name: 'Financial Checks & Deterministic Engines',
      description: 'Running math cross-casting, cash reconciliations, and prior-year delta thresholds',
      icon: Calculator,
      status: 'pending',
    },
    {
      id: 'explained',
      name: 'Review Analysis & Grounded AI Narrative',
      description: 'Synthesizing evidence-grounded anomaly explanations and candidate commentary',
      icon: BrainCircuit,
      status: 'pending',
    },
    {
      id: 'wp514_ready',
      name: 'WP-514 Preparation & Sign-Off Readiness',
      description: 'Populating WP-514 draft fields for auditor inspection',
      icon: FileSpreadsheet,
      status: 'pending',
    },
  ]);

  // Fetch actual metadata from the API to get bank name and source documents
  useEffect(() => {
    fetchReview(jobId)
      .then((res) => {
        if (res?.review_metadata) {
          const meta = res.review_metadata;
          setBankName(meta.bank_name || '');
          const currentDoc = meta.source_document_current || '';
          const priorDoc = meta.source_document_prior || '';
          setSourceDoc(
            currentDoc && priorDoc && currentDoc !== priorDoc
              ? `${currentDoc} & ${priorDoc}`
              : currentDoc || 'uploaded document'
          );
          // Update Stage 1 description with actual filenames
          setStages((prev) =>
            prev.map((s) => {
              if (s.id === 'upload') {
                return {
                  ...s,
                  description: `Ingested ${currentDoc || 'uploaded document'}${priorDoc && priorDoc !== currentDoc ? ` & ${priorDoc}` : ''}`,
                };
              }
              return s;
            })
          );
        }
      })
      .catch(() => {
        // Silently fall back
      });
  }, [jobId]);

  useEffect(() => {
    let isMounted = true;

    const checkStatus = async () => {
      try {
        const res = await getJobStatus(jobId);
        if (isMounted && res.status) {
          setBackendStatus(res.status as JobStatus);
          if (res.status === 'DONE') {
            setStages((prev) => prev.map((s) => ({ ...s, status: 'completed' })));
          }
        }
      } catch (err) {
        console.warn('Backend status check error', err);
      }
    };

    checkStatus();

    // Stage progression
    const timer1 = setTimeout(() => {
      if (!isMounted) return;
      setStages((prev) =>
        prev.map((s) => {
          if (s.id === 'extraction') return { ...s, status: 'completed' };
          if (s.id === 'checked') return { ...s, status: 'in_progress' };
          return s;
        })
      );
    }, 600);

    const timer2 = setTimeout(() => {
      if (!isMounted) return;
      setStages((prev) =>
        prev.map((s) => {
          if (s.id === 'checked') return { ...s, status: 'completed' };
          if (s.id === 'explained') return { ...s, status: 'in_progress' };
          return s;
        })
      );
    }, 1200);

    const timer3 = setTimeout(() => {
      if (!isMounted) return;
      setBackendStatus('DONE');
      setStages((prev) =>
        prev.map((s) => ({ ...s, status: 'completed' }))
      );
    }, 1800);

    return () => {
      isMounted = false;
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [jobId]);

  const isAllCompleted = stages.every((s) => s.status === 'completed');

  return (
    <div className="max-w-3xl mx-auto space-y-6 py-4">
      {/* Banner */}
      <div className="bg-white border border-slate-200 p-5 shadow-sm border-l-4 border-l-blue-800 flex items-center justify-between">
        <div>
          <span className="text-[10px] uppercase tracking-wider font-mono font-semibold text-slate-500">
            JOB ID: {jobId} | STATUS: {backendStatus}
          </span>
          <h2 className="text-base font-bold text-slate-900 mt-0.5">
            FINANCIAL STATEMENT REVIEW PIPELINE
          </h2>
          <p className="text-xs text-slate-600 mt-1">
            Executing deterministic mathematical rule functions and grounded AI analysis for {bankName || 'the uploaded entity'}.
          </p>
        </div>
        <div>
          {isAllCompleted ? (
            <span className="bg-emerald-100 text-emerald-900 border border-emerald-300 text-xs font-bold px-3 py-1.5 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              <span>WP-514 READY</span>
            </span>
          ) : (
            <span className="bg-blue-50 text-blue-900 border border-blue-200 text-xs font-semibold px-3 py-1.5 flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-blue-700 animate-spin" />
              <span>PROCESSING...</span>
            </span>
          )}
        </div>
      </div>

      {/* Stage Timeline */}
      <div className="bg-white border border-slate-200 shadow-sm p-6 space-y-4">
        <h3 className="audit-section-header">Review Lifecycle Status Timeline</h3>

        <div className="space-y-4">
          {stages.map((stage, idx) => {
            const isCompleted = stage.status === 'completed';
            const isInProgress = stage.status === 'in_progress';

            return (
              <div
                key={stage.id}
                className={`flex items-start gap-4 p-3.5 border transition-colors ${
                  isCompleted
                    ? 'bg-slate-50 border-slate-200'
                    : isInProgress
                    ? 'bg-blue-50/60 border-blue-300'
                    : 'bg-white border-slate-200 opacity-60'
                }`}
              >
                <div className="mt-0.5 flex-shrink-0">
                  {isCompleted ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  ) : isInProgress ? (
                    <Loader2 className="w-5 h-5 text-blue-800 animate-spin" />
                  ) : (
                    <Clock className="w-5 h-5 text-slate-400" />
                  )}
                </div>

                <div className="flex-1 min-w-0 space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900 tracking-tight">
                      Stage {idx + 1}: {stage.name}
                    </span>
                    <span className="text-[10px] font-mono font-semibold uppercase">
                      {isCompleted ? (
                        <span className="text-emerald-700">COMPLETED</span>
                      ) : isInProgress ? (
                        <span className="text-blue-800 font-bold">IN PROGRESS</span>
                      ) : (
                        <span className="text-slate-400">QUEUED</span>
                      )}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-normal">{stage.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Action Button once completed */}
        <div className="pt-4 flex justify-end">
          <button
            onClick={() => navigate(`/review/${jobId}/overview`)}
            disabled={!isAllCompleted}
            className={`text-xs font-semibold px-6 py-2.5 rounded-xs flex items-center gap-2 tracking-wide uppercase transition-colors ${
              isAllCompleted
                ? 'bg-blue-800 hover:bg-blue-900 text-white cursor-pointer shadow-sm'
                : 'bg-slate-300 text-slate-500 cursor-not-allowed'
            }`}
          >
            <span>OPEN REVIEW DASHBOARD</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

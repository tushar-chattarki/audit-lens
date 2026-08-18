import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Building2,
  ShieldAlert,
  AlertOctagon,
  CheckCircle2,
  FileSpreadsheet,
  BrainCircuit,
  ArrowRight,
  Calculator,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';
import { fetchReview } from '../services/api';
import { ReviewResponse } from '../types/review';
import { MetricCard } from '../components/common/MetricCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { MathReviewPanel } from '../components/review/MathReviewPanel';
import { PriorYearReviewPanel } from '../components/review/PriorYearReviewPanel';

export const OverviewPage: React.FC = () => {
  const { jobId = 'REV-2025-001' } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorState, setErrorState] = useState<string | null>(null);

  useEffect(() => {
    fetchReview(jobId)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch review', err);
        setErrorState('Failed to load review data from backend server.');
        setLoading(false);
      });
  }, [jobId]);

  if (loading) {
    return (
      <div className="p-8 text-center text-xs text-slate-500 font-mono flex items-center justify-center gap-2">
        <div className="w-4 h-4 border-2 border-blue-800 border-t-transparent rounded-full animate-spin" />
        <span>Loading financial statement review dataset for job {jobId}...</span>
      </div>
    );
  }

  if (errorState || !data) {
    return (
      <div className="bg-red-50 border border-red-300 p-6 text-red-900 space-y-3 max-w-2xl mx-auto my-8">
        <div className="flex items-center gap-2 font-bold text-sm">
          <AlertTriangle className="w-5 h-5 text-red-700" />
          <span>REVIEW DASHBOARD UN-AVAILABLE</span>
        </div>
        <p className="text-xs text-red-800">{errorState || 'Review dataset not found.'}</p>
        <button
          onClick={() => navigate('/review/new')}
          className="bg-red-800 text-white text-xs font-semibold px-4 py-2 uppercase tracking-wide cursor-pointer"
        >
          Return to Upload
        </button>
      </div>
    );
  }

  const { review_metadata, summary_kpis, statement_summaries, overall_ai_summary, wp514 } = data;

  return (
    <div className="space-y-6">
      {/* Top Header Banner — Financial Statement Review Workspace */}
      <div className="bg-white border border-slate-200 p-5 shadow-sm border-l-4 border-l-red-700 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono uppercase bg-slate-100 text-slate-700 px-2 py-0.5 border border-slate-300 font-semibold">
              JOB ID: {review_metadata.job_id}
            </span>
            <span className="text-[10px] font-mono text-slate-500">
              REVIEW DATE: {review_metadata.review_date}
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2 tracking-tight">
            <Building2 className="w-5 h-5 text-blue-900" />
            {review_metadata.bank_name}
          </h2>
          <p className="text-xs text-slate-600 mt-0.5">
            Reporting Period: <strong className="text-slate-800">{review_metadata.reporting_period}</strong> | Comparative: <strong className="text-slate-800">{review_metadata.comparative_period}</strong> | Source Document: <strong className="text-slate-800">{review_metadata.source_document_current}</strong>
          </p>
        </div>

        {/* Overall Status Indicator */}
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <div className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider">Overall Review Status</div>
            <div className="text-xs font-bold text-red-700">Action Required</div>
          </div>
          <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-2.5 flex items-center gap-2 font-bold text-xs uppercase tracking-wider shadow-xs">
            <ShieldAlert className="w-5 h-5 text-red-700" />
            <span>{review_metadata.overall_status}</span>
          </div>
        </div>
      </div>

      {/* Summary KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <MetricCard
          title="Total Checks"
          value={summary_kpis.total_findings}
          subtitle="Engine Checks Executed"
          borderLeftColor="border-blue-800"
        />
        <MetricCard
          title="Exceptions"
          value={summary_kpis.exceptions}
          subtitle="Action Required"
          borderLeftColor="border-red-600"
          badge={<AlertOctagon className="w-4 h-4 text-red-600" />}
        />
        <MetricCard
          title="Passed Checks"
          value={summary_kpis.passes}
          subtitle="Tied Out Clean"
          borderLeftColor="border-emerald-600"
          badge={<CheckCircle2 className="w-4 h-4 text-emerald-600" />}
        />
        <MetricCard
          title="Critical / High"
          value={summary_kpis.high_severity}
          subtitle="Material Mismatches"
          borderLeftColor="border-red-800"
          badge={<span className="text-[10px] font-bold text-red-800 bg-red-100 px-1.5 py-0.5">HIGH</span>}
        />
        <MetricCard
          title="Medium Severity"
          value={summary_kpis.medium_severity}
          subtitle="YoY Spikes"
          borderLeftColor="border-amber-600"
          badge={<span className="text-[10px] font-bold text-amber-800 bg-amber-100 px-1.5 py-0.5">MED</span>}
        />
        <MetricCard
          title="Low Severity"
          value={summary_kpis.low_severity}
          subtitle="Grammar / Text"
          borderLeftColor="border-slate-400"
          badge={<span className="text-[10px] font-bold text-slate-700 bg-slate-200 px-1.5 py-0.5">LOW</span>}
        />
      </div>

      {/* Executive AI Review Summary Card (Strictly labeled & grounded, graceful fallback if missing) */}
      <div className="bg-white border border-slate-300 p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between border-b border-slate-200 pb-2">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-blue-900" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              {overall_ai_summary?.label || 'AI-generated explanation'}
            </h3>
          </div>
          <span className="bg-amber-100 text-amber-900 border border-amber-300 text-[10px] font-bold px-2 py-0.5 uppercase tracking-wider">
            SUGGESTED — PENDING HUMAN REVIEWER SIGN-OFF
          </span>
        </div>

        {overall_ai_summary?.text ? (
          <p className="text-xs text-slate-800 leading-relaxed font-normal bg-slate-50 p-3.5 border border-slate-200">
            {overall_ai_summary.text}
          </p>
        ) : (
          <p className="text-xs text-slate-500 italic bg-slate-50 p-3.5 border border-slate-200">
            AI explanation unavailable for current review job.
          </p>
        )}

        <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
          <span className="italic">
            <strong>Reviewer Caveat:</strong> {overall_ai_summary?.caveats || 'Grounded on deterministic engine findings. Final sign-off required.'}
          </span>
          <span className="font-mono text-[10px] text-slate-400">Grounded Engine v1.0</span>
        </div>
      </div>

      {/* Financial Statement Review Summary Breakdown Table */}
      <div className="bg-white border border-slate-200 shadow-sm p-4 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-200 pb-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-slate-700" />
            Statement Review Breakdown (WP-514 Section 2)
          </h3>
          <button
            onClick={() => navigate(`/review/${jobId}/findings`)}
            className="text-xs text-blue-800 hover:text-blue-900 font-semibold flex items-center gap-1 cursor-pointer"
          >
            <span>View All Findings Workspace</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="audit-table">
            <thead>
              <tr>
                <th>Statement Area</th>
                <th className="text-center">Checks Performed</th>
                <th className="text-center">Passed</th>
                <th className="text-center">Exceptions</th>
                <th className="text-center">Warnings</th>
                <th className="text-right">Overall Status</th>
              </tr>
            </thead>
            <tbody>
              {statement_summaries.map((item, idx) => (
                <tr key={idx}>
                  <td className="font-semibold text-slate-900">{item.statement}</td>
                  <td className="text-center font-mono">{item.checks_performed}</td>
                  <td className="text-center font-mono text-emerald-700 font-bold">{item.passed}</td>
                  <td className="text-center font-mono text-red-700 font-bold">{item.failed}</td>
                  <td className="text-center font-mono text-amber-700 font-bold">{item.warnings}</td>
                  <td className="text-right">
                    <StatusBadge status={item.overall_status} size="sm" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mathematical Review Section Component */}
      {wp514?.math_checks && wp514.math_checks.length > 0 && (
        <MathReviewPanel mathChecks={wp514.math_checks} />
      )}

      {/* Prior-Year Review Section Component */}
      {wp514?.prior_year_checks && wp514.prior_year_checks.length > 0 && (
        <PriorYearReviewPanel priorYearChecks={wp514.prior_year_checks} />
      )}

      {/* Quick Access Action Bar */}
      <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
        <button
          onClick={() => navigate(`/review/${jobId}/analysis`)}
          className="bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 text-xs font-semibold px-4 py-2 rounded-xs flex items-center gap-2 cursor-pointer shadow-xs"
        >
          <span>FINANCIAL ANALYTICS & CHARTS</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={() => navigate(`/review/${jobId}/findings`)}
          className="bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 text-xs font-semibold px-4 py-2 rounded-xs flex items-center gap-2 cursor-pointer shadow-xs"
        >
          <span>FINDINGS WORKSPACE ({data.findings.length})</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={() => navigate(`/review/${jobId}/wp514`)}
          className="bg-blue-800 hover:bg-blue-900 text-white text-xs font-semibold px-5 py-2 rounded-xs flex items-center gap-2 cursor-pointer shadow-xs uppercase tracking-wide"
        >
          <span>WP-514 WORKING PAPER</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};

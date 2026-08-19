import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileCheck2,
  FileText,
  Search,
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  Lock
} from 'lucide-react';
import { fetchReview } from '../services/api';
import { Finding, ReviewResponse, Evidence } from '../types/review';

export const EvidencePage: React.FC = () => {
  const { jobId = 'REV-2025-001', evidenceId = 'F-002' } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState<ReviewResponse | null>(null);
  const [finding, setFinding] = useState<Finding | null>(null);
  const [activeEvidenceIndex, setActiveEvidenceIndex] = useState(0);
  const [zoomLevel, setZoomLevel] = useState(100);

  useEffect(() => {
    fetchReview(jobId).then((res) => {
      setData(res);
      const matched = res.findings.find((f) => f.finding_id === evidenceId) || res.findings[1] || res.findings[0];
      setFinding(matched);
    });
  }, [jobId, evidenceId]);

  if (!data || !finding) {
    return <div className="p-8 text-center text-xs text-slate-500 font-mono">Loading evidence viewer...</div>;
  }

  const meta = data.review_metadata;
  const currentEvidence: Evidence | undefined =
    finding.evidence && finding.evidence.length > 0
      ? finding.evidence[activeEvidenceIndex] ?? finding.evidence[0]
      : undefined;
  const currencySymbol = meta.currency === 'USD' ? '$' : meta.currency === 'EUR' ? '€' : meta.currency === 'GBP' ? '£' : '₹';
  const unitLabel = meta.unit || 'Crores (Cr)';
  const unitShort = unitLabel.includes('(') ? unitLabel.split('(')[1].replace(')', '') : unitLabel;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 p-4 shadow-sm flex items-center justify-between border-l-4 border-l-blue-900">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(`/review/${jobId}/findings`)}
            className="p-1.5 border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-xs cursor-pointer"
            title="Back to Findings"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <FileCheck2 className="w-5 h-5 text-blue-900" />
              SOURCE EVIDENCE DRILL-DOWN VIEWER
            </h2>
            <p className="text-xs text-slate-600 mt-0.5">
              Inspecting verified source page, table, and row cell highlight pointers for finding{' '}
              <strong className="font-mono text-slate-900">{finding.finding_id}</strong>.
            </p>
          </div>
        </div>

        <div className="text-xs font-mono bg-slate-100 px-3 py-1 border border-slate-300">
          DOC: {currentEvidence?.doc_id || meta.source_document_current}{currentEvidence ? ` | PAGE ${currentEvidence.page}` : ''}
        </div>
      </div>

      {/* Main Grid: Left Evidence Metadata + Right Viewer Abstraction */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 4 Cols: Evidence Pointers List & Finding Summary */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white border border-slate-200 p-4 shadow-sm space-y-3">
            <h3 className="audit-section-header">Finding Under Inspection</h3>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-blue-900">{finding.finding_id}</span>
                <span className="bg-red-100 text-red-900 border border-red-300 text-[10px] font-bold px-2 py-0.5 uppercase">
                  {finding.severity} SEVERITY
                </span>
              </div>
              <p className="font-semibold text-slate-900">{finding.check}</p>
              <div className="text-slate-600">Statement: {finding.statement}</div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 p-4 shadow-sm space-y-3">
            <h3 className="audit-section-header">Associated Evidence Locations</h3>

            <div className="space-y-2">
              {finding.evidence && finding.evidence.length > 0 ? finding.evidence.map((ev, idx) => (
                <div
                  key={idx}
                  onClick={() => setActiveEvidenceIndex(idx)}
                  className={`p-3 border cursor-pointer text-xs transition-colors ${
                    activeEvidenceIndex === idx
                      ? 'bg-blue-50 border-blue-800 border-l-4 font-semibold text-blue-950'
                      : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between font-mono text-[11px] mb-1">
                    <span>Evidence #{idx + 1}</span>
                    <span className="bg-slate-200 px-1.5 py-0.2">Page {ev.page}</span>
                  </div>
                  <div className="font-bold text-slate-900">{ev.table}</div>
                  <div className="text-[11px] text-slate-600">Line Item: {ev.row}</div>
                  <div className="text-[10px] font-mono text-slate-400 mt-1">Period: {ev.period || meta.reporting_period}</div>
                </div>
              )) : (
                <div className="text-[11px] text-slate-400 italic p-3 bg-slate-50 border border-slate-200">
                  No source document evidence pointers. This finding was generated by the AI narrative layer.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right 8 Cols: PDF Viewer & Document Page Canvas Abstraction */}
        <div className="lg:col-span-8 space-y-3">
          {!currentEvidence ? (
            <div className="bg-slate-100 border border-slate-300 min-h-[520px] flex flex-col items-center justify-center gap-3 text-center p-8">
              <FileText className="w-10 h-10 text-slate-400" />
              <div className="text-sm font-semibold text-slate-600">No Source Evidence Available</div>
              <p className="text-xs text-slate-500 max-w-xs">
                This finding was generated by the AI narrative layer and does not map to a specific source document page.
              </p>
            </div>
          ) : (
          <>
          {/* Controls Bar */}
          <div className="bg-slate-900 text-white p-3 border border-slate-800 flex items-center justify-between text-xs">
            <div className="flex items-center gap-3 font-mono text-slate-300">
              <FileText className="w-4 h-4 text-blue-400" />
              <span>{currentEvidence.doc_id || meta.source_document_current}</span>
              <span>— Page {currentEvidence.page}</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setZoomLevel((z) => Math.max(75, z - 15))}
                className="p-1 hover:bg-slate-800 rounded-xs"
                title="Zoom Out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="font-mono text-xs text-slate-300">{zoomLevel}%</span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(150, z + 15))}
                className="p-1 hover:bg-slate-800 rounded-xs"
                title="Zoom In"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Document Canvas Frame with Highlight Box */}
          <div className="bg-slate-300 p-6 border border-slate-400 min-h-[520px] flex items-center justify-center relative overflow-hidden">
            <div
              style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
              className="bg-white shadow-xl border border-slate-400 w-[600px] min-h-[700px] p-8 space-y-6 text-slate-900 font-sans transition-transform"
            >
              {/* Document Header Representation */}
              <div className="border-b-2 border-slate-900 pb-3 flex items-center justify-between">
                <div>
                  <div className="font-bold text-sm text-slate-900 uppercase tracking-tight">
                    {meta.bank_name.toUpperCase()}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    FINANCIAL STATEMENTS FOR {meta.reporting_period.toUpperCase()}
                  </div>
                </div>
                <div className="text-[10px] font-mono font-bold text-slate-700 border border-slate-300 px-2 py-1">
                  PAGE {currentEvidence.page}
                </div>
              </div>

              {/* Page Section Title */}
              <div className="font-bold text-xs uppercase tracking-wider text-slate-800 bg-slate-100 p-1.5 border-l-2 border-blue-900">
                {currentEvidence.table}
              </div>

              {/* Extracted Financial Table with Highlighting */}
              <table className="w-full text-[11px] border-collapse">
                <thead>
                  <tr className="border-b border-slate-300 text-left font-bold text-slate-700">
                    <th className="py-1">Line Item / Description</th>
                    <th className="text-right py-1">{meta.reporting_period} ({currencySymbol} {unitShort})</th>
                    <th className="text-right py-1">{meta.comparative_period} ({currencySymbol} {unitShort})</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  <tr className="bg-amber-100/70 border-l-4 border-l-amber-600 font-semibold">
                    <td className="py-1.5 text-slate-900">
                      {currentEvidence.row}
                    </td>
                    <td className="text-right font-mono py-1.5 font-bold text-red-700">
                      {typeof finding.actual === 'number' ? finding.actual.toLocaleString() : (finding.actual ?? '—')}
                    </td>
                    <td className="text-right font-mono py-1.5 text-slate-600">
                      {typeof finding.expected === 'number' ? finding.expected.toLocaleString() : (finding.expected ?? '—')}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-1.5 text-slate-600">Comparative Subtotal Line</td>
                    <td className="text-right font-mono py-1.5 text-slate-600">—</td>
                    <td className="text-right font-mono py-1.5 text-slate-600">—</td>
                  </tr>
                </tbody>
              </table>

              {/* Highlight Target Bounding Annotation Callout */}
              <div className="bg-amber-50 border-2 border-dashed border-amber-500 p-3 space-y-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900">
                    <AlertCircle className="w-4 h-4 text-amber-700" />
                    <span>CELL EVIDENCE POINTER HIGHLIGHT</span>
                  </div>
                  <span className="text-[10px] font-mono font-bold text-amber-800">Target: {currentEvidence.row}</span>
                </div>
                <p className="text-[11px] text-amber-950">
                  Mathematical check '{finding.check}' flagged variance between reported value and computed schedule reconciliation.
                </p>
              </div>

              <div className="text-[10px] text-slate-400 font-mono text-center pt-8">
                --- Audit Lens Evidence Verification Engine (WP-514 Standard) ---
              </div>
            </div>
          </div>
          </>
          )}
        </div>
      </div>
    </div>
  );
};

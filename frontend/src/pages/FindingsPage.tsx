import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Filter,
  ExternalLink,
  BrainCircuit,
  FileCheck2,
  X,
  ShieldCheck,
  Edit3,
  HelpCircle,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { fetchReview, updateFindingReviewerState } from '../services/api';
import { Finding, ReviewResponse, ReviewerStatus } from '../types/review';
import { StatusBadge } from '../components/common/StatusBadge';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const FindingsPage: React.FC = () => {
  const { jobId = 'REV-2025-001' } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedModule, setSelectedModule] = useState<string>('all');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedReviewerStatus, setSelectedReviewerStatus] = useState<string>('all');

  // Active Finding for Detail Drawer
  const [activeFinding, setActiveFinding] = useState<Finding | null>(null);
  const [isClosed, setIsClosed] = useState(false);

  // Reviewer edit form state
  const [editReviewerStatus, setEditReviewerStatus] = useState<ReviewerStatus>('Open');
  const [editReviewerComment, setEditReviewerComment] = useState<string>('');
  const [isUpdating, setIsUpdating] = useState(false);

  // Close drawer on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsClosed(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    fetchReview(jobId).then((res) => {
      setData(res);
      setLoading(false);
      // Auto open first finding if available
      if (res.findings.length > 0) {
        const initial = res.findings[1] || res.findings[0];
        setActiveFinding(initial);
        setEditReviewerStatus(initial.reviewer_status);
        setEditReviewerComment(initial.reviewer_comment || '');
      }
    });
  }, [jobId]);

  // Filter Logic
  const allFindings = data?.findings || [];
  const filteredFindings = allFindings.filter((item) => {
    if (selectedModule !== 'all' && item.module !== selectedModule) return false;
    if (selectedSeverity !== 'all' && item.severity !== selectedSeverity) return false;
    if (selectedStatus !== 'all' && item.status !== selectedStatus) return false;
    if (selectedReviewerStatus !== 'all' && item.reviewer_status !== selectedReviewerStatus) return false;
    return true;
  });

  // Pure computed active finding for drawer
  const drawerFinding = !isClosed
    ? (activeFinding && filteredFindings.some((f) => f.finding_id === activeFinding.finding_id)
      ? activeFinding
      : filteredFindings[0] || null)
    : null;

  const meta = data?.review_metadata;
  const currencySymbol = meta?.currency === 'USD' ? '$' : meta?.currency === 'EUR' ? '€' : meta?.currency === 'GBP' ? '£' : '₹';
  const unitLabel = meta?.unit || 'Crores (Cr)';
  const unitShort = unitLabel.includes('(') ? unitLabel.split('(')[1].replace(')', '') : unitLabel;

  const formatAmount = (val: number | string | null | undefined): string => {
    if (val === null || val === undefined) return '—';
    if (typeof val === 'number') {
      return `${currencySymbol}${val.toLocaleString()} ${unitShort}`;
    }
    return String(val);
  };

  useEffect(() => {
    if (drawerFinding) {
      setEditReviewerStatus(drawerFinding.reviewer_status);
      setEditReviewerComment(drawerFinding.reviewer_comment || '');
    }
  }, [drawerFinding?.finding_id]);

  if (loading || !data) {
    return (
      <div className="p-8 text-center text-xs text-slate-500 font-mono flex items-center justify-center gap-2">
        <div className="w-4 h-4 border-2 border-blue-800 border-t-transparent rounded-full animate-spin" />
        <span>Loading detailed findings workspace...</span>
      </div>
    );
  }

  const handleOpenDrawer = (finding: Finding) => {
    setIsClosed(false);
    setActiveFinding(finding);
    setEditReviewerStatus(finding.reviewer_status);
    setEditReviewerComment(finding.reviewer_comment || '');
  };

  const handleSaveReviewerSignoff = async () => {
    if (!drawerFinding) return;
    setIsUpdating(true);
    try {
      const updated = await updateFindingReviewerState(jobId, drawerFinding.finding_id, editReviewerStatus, editReviewerComment);
      setActiveFinding(updated);
      // Update local state in dataset
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          findings: prev.findings.map((f) => (f.finding_id === updated.finding_id ? updated : f)),
        };
      });
    } catch (e) {
      console.error('Failed to save signoff', e);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="space-y-6 relative">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 p-4 shadow-sm flex items-center justify-between border-l-4 border-l-blue-900">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Filter className="w-5 h-5 text-blue-900" />
            DETAILED REVIEW FINDINGS WORKSPACE
          </h2>
          <p className="text-xs text-slate-600 mt-0.5">
            Filter, inspect source evidence pointers, review candidate AI narrative explanations, and execute human auditor sign-off.
          </p>
        </div>
        <div className="text-xs font-mono bg-slate-100 px-3 py-1 border border-slate-300">
          TOTAL FINDINGS: {data.findings.length} | EXCEPTIONS: {data.summary_kpis.exceptions}
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white border border-slate-200 p-3.5 shadow-sm flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          {/* Module Filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-700">Module:</span>
            <select
              data-testid="module-filter"
              value={selectedModule}
              onChange={(e) => setSelectedModule(e.target.value)}
              className="px-2.5 py-1 border border-slate-300 rounded-xs bg-white text-slate-800 focus:ring-1 focus:ring-blue-800 outline-none"
            >
              <option value="all">All Modules</option>
              <option value="math_engine">Math Engine</option>
              <option value="consistency_engine">Consistency Engine</option>
              <option value="prior_year_engine">Prior Year Engine</option>
              <option value="ai_layer">AI Layer</option>
              <option value="language_engine">Language / Grammar</option>
            </select>
          </div>

          {/* Severity Filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-700">Severity:</span>
            <select
              data-testid="severity-filter"
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="px-2.5 py-1 border border-slate-300 rounded-xs bg-white text-slate-800 focus:ring-1 focus:ring-blue-800 outline-none"
            >
              <option value="all">All Severities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Result Filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-700">Result:</span>
            <select
              data-testid="result-filter"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-2.5 py-1 border border-slate-300 rounded-xs bg-white text-slate-800 focus:ring-1 focus:ring-blue-800 outline-none"
            >
              <option value="all">All Results</option>
              <option value="exception">Exceptions Only</option>
              <option value="warning">Warnings / Unusual</option>
              <option value="pass">Passed Only</option>
              <option value="not_applicable">Not Applicable</option>
            </select>
          </div>

          {/* Reviewer Status Filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-700">Reviewer Status:</span>
            <select
              data-testid="reviewer-status-filter"
              value={selectedReviewerStatus}
              onChange={(e) => setSelectedReviewerStatus(e.target.value)}
              className="px-2.5 py-1 border border-slate-300 rounded-xs bg-white text-slate-800 focus:ring-1 focus:ring-blue-800 outline-none"
            >
              <option value="all">All Sign-off Statuses</option>
              <option value="Open">Open</option>
              <option value="Reviewed">Reviewed</option>
              <option value="Accepted">Accepted</option>
              <option value="Resolved">Resolved</option>
              <option value="Requires Revision">Requires Revision</option>
            </select>
          </div>
        </div>

        <div className="text-[11px] text-slate-500 font-mono">
          Showing {filteredFindings.length} of {data.findings.length} findings
        </div>
      </div>

      {/* Main Table or Empty State */}
      {filteredFindings.length === 0 ? (
        <div className="bg-white border border-slate-200 p-8 text-center space-y-2">
          <CheckCircle2 className="w-8 h-8 text-slate-400 mx-auto" />
          <div className="text-xs font-bold text-slate-700">No findings matched current filter criteria.</div>
          <button
            onClick={() => {
              setSelectedModule('all');
              setSelectedSeverity('all');
              setSelectedStatus('all');
              setSelectedReviewerStatus('all');
            }}
            className="text-xs text-blue-800 underline hover:text-blue-900 cursor-pointer"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 shadow-sm overflow-x-auto">
          <table className="audit-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Module</th>
                <th>Review Check</th>
                <th>Statement / Area</th>
                <th className="text-center">Severity</th>
                <th className="text-right">Reported / Actual</th>
                <th className="text-right">Expected</th>
                <th className="text-right">Variance</th>
                <th className="text-center">Result</th>
                <th className="text-center">Evidence</th>
                <th className="text-center">AI Candidate</th>
                <th className="text-center">Sign-off</th>
                <th className="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredFindings.map((finding) => (
                <tr
                  key={finding.finding_id}
                  onClick={() => handleOpenDrawer(finding)}
                  className={`cursor-pointer transition-colors ${
                    drawerFinding?.finding_id === finding.finding_id ? 'bg-blue-50/70 border-l-4 border-l-blue-800' : ''
                  }`}
                >
                  <td className="font-mono font-bold text-slate-900">{finding.finding_id}</td>
                  <td className="font-mono text-[11px] text-slate-600 uppercase">
                    {finding.module ? finding.module.replace('_engine', '') : 'ENGINE'}
                  </td>
                  <td className="font-semibold text-slate-800 max-w-xs truncate">{finding.check || '—'}</td>
                  <td className="text-slate-700">{finding.statement || '—'}</td>
                  <td className="text-center">
                    <SeverityBadge severity={finding.severity || 'low'} />
                  </td>
                  <td className="text-right font-mono font-semibold">
                    {formatAmount(finding.actual)}
                  </td>
                  <td className="text-right font-mono text-slate-600">
                    {formatAmount(finding.expected)}
                  </td>
                  <td className="text-right font-mono font-bold text-red-700">
                    {finding.difference !== null && finding.difference !== undefined
                      ? formatAmount(finding.difference)
                      : '—'}
                  </td>
                  <td className="text-center">
                    <StatusBadge status={finding.status || 'exception'} size="sm" />
                  </td>
                  <td className="text-center">
                    <span className="inline-flex items-center gap-1 text-[11px] font-mono text-blue-800 font-semibold bg-blue-50 px-2 py-0.5 border border-blue-200">
                      <FileCheck2 className="w-3 h-3" />
                      <span>P.{finding.evidence && finding.evidence[0] ? finding.evidence[0].page : 2}</span>
                    </span>
                  </td>
                  <td className="text-center">
                    {finding.ai_explanation ? (
                      <span className="text-[10px] bg-amber-100 text-amber-900 border border-amber-300 font-bold px-1.5 py-0.5">
                        AI SUGGESTED
                      </span>
                    ) : (
                      <span className="text-[10px] text-slate-400">—</span>
                    )}
                  </td>
                  <td className="text-center">
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 border uppercase font-bold ${
                        finding.reviewer_status === 'Reviewed' || finding.reviewer_status === 'Accepted'
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                          : 'bg-slate-100 text-slate-700 border-slate-300'
                      }`}
                    >
                      {finding.reviewer_status}
                    </span>
                  </td>
                  <td className="text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenDrawer(finding);
                      }}
                      className="text-xs text-blue-800 font-semibold hover:underline cursor-pointer"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Right Detail Drawer with Backdrop Overlay */}
      {drawerFinding && !isClosed && (
        <>
          {/* Backdrop overlay */}
          <div
            data-testid="drawer-backdrop"
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-[1px] z-40 transition-opacity"
            onClick={() => setIsClosed(true)}
            title="Click outside to close inspector"
          />

          {/* Drawer Panel */}
          <div className="fixed inset-y-0 right-0 w-full max-w-xl bg-white border-l border-slate-300 shadow-2xl z-50 flex flex-col animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="bg-slate-900 text-white p-4 flex items-center justify-between border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="bg-blue-700 font-mono text-xs px-2 py-0.5 font-bold">{drawerFinding.finding_id}</span>
                <h3 className="text-xs font-bold uppercase tracking-wide text-slate-100">
                  Finding Detail & Evidence Inspector
                </h3>
              </div>
              <button
                onClick={() => setIsClosed(true)}
                className="text-slate-400 hover:text-white px-2 py-1 rounded-xs bg-slate-800 hover:bg-slate-700 text-xs flex items-center gap-1 cursor-pointer transition-colors"
                title="Close Inspector (Esc)"
              >
                <span className="text-[10px] font-mono uppercase">Close</span>
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="flex-1 overflow-y-auto p-5 space-y-5 text-xs text-slate-800">
              {/* Finding Overview */}
              <div className="bg-slate-50 border border-slate-300 p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 text-xs">{drawerFinding.check}</span>
                  <StatusBadge status={drawerFinding.status} />
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2 text-[11px]">
                  <div>
                    <span className="text-slate-500 block">Module Engine:</span>
                    <span className="font-mono font-semibold text-slate-800 uppercase">{drawerFinding.module}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Statement Area:</span>
                    <span className="font-semibold text-slate-800">{drawerFinding.statement}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Severity Level:</span>
                    <SeverityBadge severity={drawerFinding.severity} />
                  </div>
                  <div>
                    <span className="text-slate-500 block">Numeric Variance:</span>
                    <span className="font-mono font-bold text-red-700">
                      {drawerFinding.difference !== null && drawerFinding.difference !== undefined
                        ? formatAmount(drawerFinding.difference)
                        : '—'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Deterministic Expected vs Actual Values */}
              <div className="bg-white border border-slate-300 p-4 space-y-3 shadow-xs">
                <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider border-b border-slate-200 pb-1.5 flex items-center justify-between">
                  <span>Deterministic Figures</span>
                  <span className="text-[10px] font-mono text-slate-500 font-normal">Audit-Lens Math Engine</span>
                </h4>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-50 p-2.5 border border-slate-200">
                    <span className="text-slate-500 block text-[11px]">Reported / Actual Value:</span>
                    <span className="font-mono font-bold text-sm text-slate-900">
                      {formatAmount(drawerFinding.actual)}
                    </span>
                  </div>
                  <div className="bg-slate-50 p-2.5 border border-slate-200">
                    <span className="text-slate-500 block text-[11px]">Expected Rule Value:</span>
                    <span className="font-mono font-bold text-sm text-slate-900">
                      {formatAmount(drawerFinding.expected)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Evidence Pointers Mapping */}
              <div className="border border-slate-300 p-4 space-y-3 bg-white shadow-xs">
                <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
                  <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-1.5">
                    <FileCheck2 className="w-4 h-4 text-blue-900" />
                    Source Evidence Mapping ({drawerFinding.evidence.length} Pointers)
                  </h4>
                </div>

                <div className="space-y-2">
                  {drawerFinding.evidence.map((ev, idx) => (
                    <div key={idx} className="bg-slate-50 p-2.5 border border-slate-200 flex items-center justify-between">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900">{ev.table}</span>
                          <span className="bg-blue-100 text-blue-900 text-[10px] font-mono font-semibold px-1.5 py-0.2">
                            Page {ev.page}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-600 font-mono">
                          Row: {ev.row} {ev.period ? `(${ev.period})` : ''}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">Doc: {ev.doc_id}</div>
                      </div>

                      <button
                        onClick={() => navigate(`/review/${jobId}/evidence/${drawerFinding.finding_id}`)}
                        className="text-xs text-blue-800 hover:text-blue-900 font-semibold flex items-center gap-1 bg-white border border-slate-300 px-2 py-1 cursor-pointer hover:bg-slate-50 shadow-2xs"
                      >
                        <span>Inspect PDF</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Grounded AI Narrative Explanation */}
              {drawerFinding.ai_explanation ? (
                <div className="border border-amber-300 bg-amber-50/70 p-4 space-y-3">
                  <div className="flex items-center justify-between border-b border-amber-200 pb-1.5">
                    <div className="flex items-center gap-2">
                      <BrainCircuit className="w-4 h-4 text-amber-800" />
                      <span className="font-bold text-amber-900 text-xs">
                        AI-generated explanation ({drawerFinding.ai_explanation.label})
                      </span>
                    </div>
                    <span className="bg-amber-200 text-amber-900 font-bold text-[10px] px-2 py-0.5 border border-amber-300 uppercase">
                      SUGGESTED CANDIDATE
                    </span>
                  </div>

                  <p className="text-xs text-amber-950 leading-relaxed font-normal bg-white p-3 border border-amber-200">
                    {drawerFinding.ai_explanation.text || drawerFinding.ai_explanation.suggested_revision}
                  </p>

                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600 pt-1">
                    <div>
                      <span className="text-slate-500 block">AI Confidence Score:</span>
                      <span className="font-mono font-bold text-slate-800">
                        {(drawerFinding.ai_explanation.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Target WP-514 Field:</span>
                      <span className="font-mono font-semibold text-slate-800">
                        {drawerFinding.ai_explanation.wp514_target_field || 'Section 3 Log'}
                      </span>
                    </div>
                  </div>

                  <div className="text-[11px] text-amber-900 bg-amber-100 p-2 border border-amber-200 flex items-start gap-1.5">
                    <HelpCircle className="w-4 h-4 text-amber-700 flex-shrink-0 mt-0.5" />
                    <span>
                      <strong>Reviewer Note:</strong> {drawerFinding.ai_explanation.caveats}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="bg-slate-100 border border-slate-200 p-3 text-slate-500 italic text-[11px]">
                  No AI explanation required for clean mathematical pass.
                </div>
              )}

              {/* Editable Reviewer Sign-Off Form */}
              <div className="border border-slate-300 p-4 bg-slate-50 space-y-3">
                <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-200 pb-2">
                  <Edit3 className="w-4 h-4 text-blue-900" />
                  Human Reviewer Sign-Off & Commentary
                </h4>

                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                      Reviewer Decision Status:
                    </label>
                    <select
                      value={editReviewerStatus}
                      onChange={(e) => setEditReviewerStatus(e.target.value as ReviewerStatus)}
                      className="w-full text-xs px-3 py-1.5 border border-slate-300 bg-white font-medium focus:ring-1 focus:ring-blue-800 outline-none"
                    >
                      <option value="Open">Open (Pending Review)</option>
                      <option value="Reviewed">Reviewed (Inspected Evidence)</option>
                      <option value="Accepted">Accepted (Explanation Validated)</option>
                      <option value="Resolved">Resolved (Reconciled with Bank)</option>
                      <option value="Requires Revision">Requires Revision (Sent to Finance Team)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                      Auditor Reviewer Comment:
                    </label>
                    <textarea
                      rows={3}
                      value={editReviewerComment}
                      onChange={(e) => setEditReviewerComment(e.target.value)}
                      placeholder="Enter formal audit review working paper note..."
                      className="w-full text-xs px-3 py-2 border border-slate-300 bg-white focus:ring-1 focus:ring-blue-800 outline-none"
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleSaveReviewerSignoff}
                      disabled={isUpdating}
                      className="flex-1 bg-blue-800 hover:bg-blue-900 text-white font-semibold text-xs py-2 uppercase tracking-wide flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                    >
                      <ShieldCheck className="w-4 h-4" />
                      <span>{isUpdating ? 'SAVING SIGN-OFF...' : 'SAVE REVIEWER SIGN-OFF'}</span>
                    </button>
                    <button
                      onClick={() => setIsClosed(true)}
                      className="bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 font-semibold text-xs py-2 px-3 uppercase tracking-wide cursor-pointer"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

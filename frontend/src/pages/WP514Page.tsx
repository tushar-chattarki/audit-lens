import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  FileSpreadsheet,
  Building2,
  CheckCircle2,
  AlertOctagon,
  ShieldCheck,
  Download,
  Printer,
  Edit3,
  HelpCircle
} from 'lucide-react';
import { fetchReview } from '../services/api';
import { ReviewResponse, WP514Data } from '../types/review';
import { StatusBadge } from '../components/common/StatusBadge';
import { SeverityBadge } from '../components/common/SeverityBadge';

import { exportWP514ToExcel } from '../utils/excelExporter';

export const WP514Page: React.FC = () => {
  const { jobId = 'REV-2025-001' } = useParams();
  const [data, setData] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Editable Reviewer Sign-Off state
  const [auditorName, setAuditorName] = useState<string>('Senior Bank Auditor');
  const [finalDecision, setFinalDecision] = useState<string>(
    'REQUIRES REVISION BY FINANCE TEAM'
  );
  const [finalComments, setFinalComments] = useState<string>('');
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    fetchReview(jobId).then((res) => {
      setData(res);
      if (res.wp514?.engagement_details?.reviewed_by && res.wp514.engagement_details.reviewed_by !== 'Pending Auditor Sign-off') {
        setAuditorName(res.wp514.engagement_details.reviewed_by);
      }
      if (res.wp514?.overall_conclusion) {
        setFinalDecision(res.wp514.overall_conclusion.final_reviewer_decision || 'REQUIRES REVISION BY FINANCE TEAM');
        setFinalComments(
          res.wp514.overall_conclusion.reviewer_comments ||
          (res.summary_kpis?.exceptions === 0
            ? `Deterministic checks for ${res.review_metadata.bank_name} (${res.review_metadata.reporting_period}) verified clean with 0 exceptions.`
            : `Audit review for ${res.review_metadata.bank_name} (${res.review_metadata.reporting_period}) identified ${res.summary_kpis?.exceptions || 0} exceptions requiring auditor review prior to sign-off.`)
        );
      }
      setLoading(false);
    });
  }, [jobId]);

  if (loading || !data || !data.wp514) {
    return <div className="p-8 text-center text-xs text-slate-500 font-mono">Loading WP-514 working paper...</div>;
  }

  const wp: WP514Data = data.wp514;
  const eng = wp.engagement_details;
  const conc = wp.overall_conclusion;
  const meta = data.review_metadata;

  const currencySymbol = meta.currency === 'USD' ? '$' : meta.currency === 'EUR' ? '€' : meta.currency === 'GBP' ? '£' : '₹';
  const unitLabel = meta.unit || eng.unit || 'Crores (Cr)';
  const unitShort = unitLabel.includes('(') ? unitLabel.split('(')[1].replace(')', '') : unitLabel;

  const formatAmount = (val: number | string | null | undefined): string => {
    if (val === null || val === undefined) return '—';
    if (typeof val === 'number') {
      return `${currencySymbol}${val.toLocaleString()} ${unitShort}`;
    }
    let strVal = String(val);
    if (strVal.includes('Cr') || strVal.includes('Crores')) {
      strVal = strVal.replace(/\bCr\b/g, unitShort).replace(/\bCrores\b/g, unitShort);
    }
    return strVal;
  };

  const handleSaveSignoff = () => {
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  const handleExportXLSX = () => {
    if (data) {
      exportWP514ToExcel(data, finalDecision, finalComments, auditorName);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header Bar */}
      <div className="bg-slate-900 text-white p-4 shadow-md flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileSpreadsheet className="w-6 h-6 text-blue-400" />
          <div>
            <h2 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
              WP-514 — FINANCIAL STATEMENT REVIEW WORKING PAPER
            </h2>
            <p className="text-xs text-slate-300">
              Standard Banking Audit Working Paper — {eng.bank_name || meta.bank_name} ({eng.reporting_period || meta.reporting_period})
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => window.print()}
            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs px-3 py-1.5 text-slate-200 flex items-center gap-1.5 cursor-pointer"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Paper</span>
          </button>
          <button
            onClick={handleExportXLSX}
            className="bg-blue-800 hover:bg-blue-900 text-white text-xs font-semibold px-4 py-1.5 flex items-center gap-1.5 cursor-pointer uppercase tracking-wide shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export XLSX</span>
          </button>
        </div>
      </div>

      {/* SECTION 1: Engagement / Review Details */}
      <div className="bg-white border border-slate-300 shadow-sm p-4 space-y-3">
        <h3 className="audit-section-header text-blue-900">1. ENGAGEMENT / REVIEW DETAILS</h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
          <div className="bg-slate-50 p-2.5 border border-slate-200">
            <span className="text-slate-500 text-[10px] block">WP Reference:</span>
            <span className="font-bold text-slate-900">WP-514 (2026)</span>
          </div>
          <div className="bg-slate-50 p-2.5 border border-slate-200">
            <span className="text-slate-500 text-[10px] block">Bank Name / ID:</span>
            <span className="font-bold text-slate-900">{eng.bank_name || meta.bank_name} ({eng.bank_id || meta.bank_id || 'BANK'})</span>
          </div>
          <div className="bg-slate-50 p-2.5 border border-slate-200">
            <span className="text-slate-500 text-[10px] block">Reporting / Comparative:</span>
            <span className="font-bold text-slate-900">{eng.reporting_period || meta.reporting_period} vs {eng.comparative_period || meta.comparative_period}</span>
          </div>
          <div className="bg-slate-50 p-2.5 border border-slate-200">
            <span className="text-slate-500 text-[10px] block">Currency & Unit:</span>
            <span className="font-bold text-slate-900">{eng.currency || meta.currency} ({eng.unit || meta.unit})</span>
          </div>
          <div className="bg-slate-50 p-2.5 border border-slate-200">
            <span className="text-slate-500 text-[10px] block">Source Document:</span>
            <span className="font-bold text-slate-900 truncate block" title={eng.source_document_current || meta.source_document_current}>
              {eng.source_document_current || meta.source_document_current}
            </span>
          </div>
          <div className="bg-slate-50 p-2.5 border border-slate-200">
            <span className="text-slate-500 text-[10px] block">Review Date:</span>
            <span className="font-bold text-slate-900">{eng.review_date || meta.review_date}</span>
          </div>
          <div className="bg-slate-50 p-2.5 border border-slate-200">
            <span className="text-slate-500 text-[10px] block">Prepared By:</span>
            <span className="font-bold text-slate-900">{eng.prepared_by || meta.prepared_by}</span>
          </div>
          <div className="bg-slate-50 p-2.5 border border-slate-200">
            <span className="text-slate-500 text-[10px] block">Reviewed By / Auditor:</span>
            <span className="font-bold text-slate-900">{auditorName || eng.reviewed_by || meta.reviewed_by}</span>
          </div>
          <div className="bg-red-50 p-2.5 border border-red-300">
            <span className="text-slate-500 text-[10px] block">Overall Status:</span>
            <span className="font-bold text-red-900 uppercase">{eng.overall_status || meta.overall_status}</span>
          </div>
        </div>
      </div>

      {/* SECTION 2: Financial Statement Review Summary */}
      <div className="bg-white border border-slate-300 shadow-sm p-4 space-y-3">
        <h3 className="audit-section-header text-blue-900">2. FINANCIAL STATEMENT REVIEW SUMMARY</h3>

        <table className="audit-table">
          <thead>
            <tr>
              <th>Statement</th>
              <th className="text-center">Checks Performed</th>
              <th className="text-center">Passed</th>
              <th className="text-center">Failed</th>
              <th className="text-center">Warnings</th>
              <th className="text-right">Overall Status</th>
            </tr>
          </thead>
          <tbody>
            {wp.financial_statement_summary.map((row, idx) => (
              <tr key={idx}>
                <td className="font-semibold text-slate-900">{row.statement}</td>
                <td className="text-center font-mono">{row.checks_performed}</td>
                <td className="text-center font-mono text-emerald-700 font-bold">{row.passed}</td>
                <td className="text-center font-mono text-red-700 font-bold">{row.failed}</td>
                <td className="text-center font-mono text-amber-700 font-bold">{row.warnings}</td>
                <td className="text-right">
                  <StatusBadge status={row.overall_status} size="sm" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* SECTION 3: Detailed Review Findings / Exception Log */}
      <div className="bg-white border border-slate-300 shadow-sm p-4 space-y-3">
        <h3 className="audit-section-header text-blue-900">3. DETAILED REVIEW FINDINGS / EXCEPTION LOG</h3>

        <div className="overflow-x-auto">
          <table className="audit-table text-[11px]">
            <thead>
              <tr>
                <th>Issue ID</th>
                <th>Statement</th>
                <th>Review Check</th>
                <th className="text-right">Reported</th>
                <th className="text-right">Expected</th>
                <th className="text-right">Variance</th>
                <th className="text-center">Severity</th>
                <th>Evidence Reference</th>
                <th>AI Explanation (Suggested)</th>
                <th>Reviewer Sign-off</th>
              </tr>
            </thead>
            <tbody>
              {data.findings.map((f) => (
                <tr key={f.finding_id}>
                  <td className="font-mono font-bold text-slate-900">{f.finding_id}</td>
                  <td className="text-slate-800">{f.statement}</td>
                  <td className="font-semibold text-slate-900">{f.check}</td>
                  <td className="text-right font-mono font-semibold">
                    {formatAmount(f.actual)}
                  </td>
                  <td className="text-right font-mono text-slate-600">
                    {formatAmount(f.expected)}
                  </td>
                  <td className="text-right font-mono font-bold text-red-700">
                    {f.difference !== null && f.difference !== undefined ? formatAmount(f.difference) : '—'}
                  </td>
                  <td className="text-center">
                    <SeverityBadge severity={f.severity} />
                  </td>
                  <td className="font-mono text-[10px] text-slate-700">
                    Page {f.evidence[0]?.page || 2}, {f.evidence[0]?.table}
                  </td>
                  <td className="text-slate-700 max-w-md whitespace-normal break-words leading-relaxed text-xs" title={f.ai_explanation?.text || f.ai_explanation?.suggested_revision || ''}>
                    {f.ai_explanation?.text || f.ai_explanation?.suggested_revision || '—'}
                  </td>
                  <td className="font-mono text-[10px] uppercase font-bold text-slate-800">
                    {f.reviewer_status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* SECTION 4: Mathematical Review Checks */}
      <div className="bg-white border border-slate-300 shadow-sm p-4 space-y-3">
        <h3 className="audit-section-header text-blue-900">4. MATHEMATICAL REVIEW CHECKS (DETERMINISTIC)</h3>

        <table className="audit-table">
          <thead>
            <tr>
              <th>Check ID</th>
              <th>Statement</th>
              <th>Check Description</th>
              <th>Formula / Rule</th>
              <th className="text-right">Reported Result</th>
              <th className="text-right">Calculated Result</th>
              <th className="text-right">Variance</th>
              <th className="text-right">Status</th>
            </tr>
          </thead>
          <tbody>
            {wp.math_checks.map((m) => (
              <tr key={m.check_id}>
                <td className="font-mono font-bold text-slate-900">{m.check_id}</td>
                <td>{m.statement}</td>
                <td className="font-semibold text-slate-900">{m.check_description}</td>
                <td className="font-mono text-[11px] text-slate-600">{m.formula_rule}</td>
                <td className="text-right font-mono">{formatAmount(m.reported_result)}</td>
                <td className="text-right font-mono">{formatAmount(m.calculated_result)}</td>
                <td className="text-right font-mono font-bold text-red-700">
                  {formatAmount(m.variance)}
                </td>
                <td className="text-right">
                  <StatusBadge status={m.status} size="sm" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* SECTION 5: Prior-Year Review */}
      <div className="bg-white border border-slate-300 shadow-sm p-4 space-y-3">
        <h3 className="audit-section-header text-blue-900">5. PRIOR-YEAR REVIEW (DELTA ANALYSIS)</h3>

        <table className="audit-table">
          <thead>
            <tr>
              <th>Statement</th>
              <th>Line Item</th>
              <th className="text-right">{eng.reporting_period || meta.reporting_period} Value</th>
              <th className="text-right">{eng.comparative_period || meta.comparative_period} Value</th>
              <th className="text-right">Abs Change</th>
              <th className="text-right">% Change</th>
              <th>Threshold</th>
              <th>Reason for Flag</th>
            </tr>
          </thead>
          <tbody>
            {wp.prior_year_checks.map((py, idx) => (
              <tr key={idx}>
                <td>{py.statement}</td>
                <td className="font-semibold text-slate-900">{py.line_item}</td>
                <td className="text-right font-mono">{formatAmount(py.current_year_value)}</td>
                <td className="text-right font-mono text-slate-600">{formatAmount(py.prior_year_value)}</td>
                <td className="text-right font-mono font-bold text-slate-900">{formatAmount(py.absolute_change)}</td>
                <td className="text-right font-mono font-bold text-red-700">+{py.percentage_change}%</td>
                <td className="font-mono text-[10px]">{py.review_threshold}</td>
                <td className="text-slate-800 text-xs">{py.reason_for_flag}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* SECTION 6: Banking Analytics */}
      <div className="bg-white border border-slate-300 shadow-sm p-4 space-y-3">
        <h3 className="audit-section-header text-blue-900">6. BANKING ANALYTICS & RATIO CHECKS</h3>

        <table className="audit-table">
          <thead>
            <tr>
              <th>Analytics Metric</th>
              <th className="text-right">{eng.reporting_period || meta.reporting_period}</th>
              <th className="text-right">{eng.comparative_period || meta.comparative_period}</th>
              <th className="text-right">Change</th>
              <th>Threshold</th>
              <th className="text-center">Status</th>
              <th>Explanation</th>
            </tr>
          </thead>
          <tbody>
            {wp.banking_analytics.map((ba, idx) => (
              <tr key={idx}>
                <td className="font-semibold text-slate-900">{ba.metric}</td>
                <td className="text-right font-mono">{ba.current_year}%</td>
                <td className="text-right font-mono">{ba.prior_year}%</td>
                <td className="text-right font-mono font-bold">{ba.change}</td>
                <td className="font-mono text-[10px]">{ba.threshold}</td>
                <td className="text-center">
                  <StatusBadge status={ba.status === 'PASS' ? 'pass' : 'exception'} size="sm" />
                </td>
                <td className="text-slate-700 text-xs">{ba.explanation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* SECTION 7: WP-514 Field Mapping */}
      <div className="bg-white border border-slate-300 shadow-sm p-4 space-y-3">
        <h3 className="audit-section-header text-blue-900">7. WP-514 FIELD MAPPING AUDIT TRAIL</h3>

        <table className="audit-table">
          <thead>
            <tr>
              <th>WP-514 Target Field</th>
              <th>Source Statement</th>
              <th>Source Line Item</th>
              <th className="text-right">Extracted Value</th>
              <th>Validation Result</th>
              <th>Exception ID</th>
            </tr>
          </thead>
          <tbody>
            {wp.field_mappings.map((fm, idx) => (
              <tr key={idx}>
                <td className="font-semibold text-slate-900">{fm.wp514_field}</td>
                <td>{fm.source_statement}</td>
                <td>{fm.source_line_item}</td>
                <td className="text-right font-mono font-bold">{formatAmount(fm.extracted_value)}</td>
                <td className="text-red-700 font-semibold">{fm.validation}</td>
                <td className="font-mono font-bold text-blue-900">{fm.exception_id || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* SECTION 8: Overall Conclusion & Editable Human Reviewer Sign-Off */}
      <div className="bg-white border-2 border-slate-400 shadow-md p-6 space-y-4">
        <div className="flex items-center justify-between border-b-2 border-slate-300 pb-3">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-blue-900" />
            8. OVERALL CONCLUSION & AUDITOR SIGN-OFF
          </h3>
          <span className="bg-red-100 text-red-900 border border-red-300 font-mono text-xs font-bold px-3 py-1">
            HUMAN REVIEWER CONTROLLED
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          {/* Left Column: Automated Summary */}
          <div className="space-y-3 bg-slate-50 p-4 border border-slate-200">
            <div className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
              Engine Audit Metrics Summary
            </div>

            <div className="space-y-1 font-mono text-xs">
              <div className="flex justify-between">
                <span>Total Exceptions Identified:</span>
                <span className="font-bold text-red-700">{conc.total_exceptions}</span>
              </div>
              <div className="flex justify-between">
                <span>High Severity Exceptions:</span>
                <span className="font-bold text-red-800">{conc.high_exceptions}</span>
              </div>
              <div className="flex justify-between">
                <span>Medium Severity Exceptions:</span>
                <span className="font-bold text-amber-700">{conc.medium_exceptions}</span>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-200 space-y-1">
              <span className="font-bold text-slate-800 text-[11px] block">Key Issues Requiring Attention:</span>
              <ul className="list-disc pl-4 space-y-1 text-slate-700 text-[11px]">
                {conc.key_issues_requiring_attention.map((issue, idx) => (
                  <li key={idx}>{issue}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Right Column: Editable Human Reviewer Decision */}
          <div className="space-y-4 border border-slate-300 p-4 bg-white">
            <div className="flex items-center gap-2 font-bold text-slate-900 uppercase tracking-wider text-xs border-b border-slate-200 pb-2">
              <Edit3 className="w-4 h-4 text-blue-900" />
              <span>Final Reviewer Decision (Human Sign-Off)</span>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Lead Auditor / Reviewer Name:
                </label>
                <input
                  type="text"
                  value={auditorName}
                  onChange={(e) => setAuditorName(e.target.value)}
                  placeholder="Enter lead auditor name..."
                  className="w-full text-xs px-3 py-2 border border-slate-300 font-semibold text-slate-900 bg-white focus:ring-1 focus:ring-blue-800 outline-none mb-2"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Final Decision Status:
                </label>
                <select
                  value={finalDecision}
                  onChange={(e) => setFinalDecision(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-slate-300 font-bold text-slate-900 bg-white focus:ring-1 focus:ring-blue-800"
                >
                  <option value="REQUIRES REVISION BY FINANCE TEAM">
                    REQUIRES REVISION BY FINANCE TEAM
                  </option>
                  <option value="APPROVED WITH REVIEWER QUALIFICATIONS">
                    APPROVED WITH REVIEWER QUALIFICATIONS
                  </option>
                  <option value="APPROVED FOR AUDIT SIGN-OFF">
                    APPROVED FOR AUDIT SIGN-OFF
                  </option>
                  <option value="REJECTED — UNRECONCILED DISCREPANCIES">
                    REJECTED — UNRECONCILED DISCREPANCIES
                  </option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Final Lead Auditor Comments:
                </label>
                <textarea
                  rows={4}
                  value={finalComments}
                  onChange={(e) => setFinalComments(e.target.value)}
                  className="w-full text-xs p-3 border border-slate-300 bg-slate-50 focus:bg-white focus:ring-1 focus:ring-blue-800 outline-none text-slate-900 leading-relaxed font-normal"
                />
              </div>

              <div className="flex items-center justify-between pt-1">
                <span className="text-[11px] text-slate-500 italic">
                  {isSaved ? '✔ WP-514 Sign-off saved!' : 'Human reviewer sign-off required for final archive.'}
                </span>
                <button
                  onClick={handleSaveSignoff}
                  className="bg-blue-800 hover:bg-blue-900 text-white font-semibold text-xs px-5 py-2 uppercase tracking-wide cursor-pointer shadow-xs flex items-center gap-1.5"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>SIGN OFF & LOCK WP-514</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

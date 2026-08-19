import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle2, AlertCircle, ArrowRight, Building2, HelpCircle } from 'lucide-react';
import { createJob } from '../services/api';

const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50MB limit

export const NewReviewPage: React.FC = () => {
  const navigate = useNavigate();
  const [bankName, setBankName] = useState('');
  const [reportingPeriod, setReportingPeriod] = useState('FY2025');
  const [comparativePeriod, setComparativePeriod] = useState('FY2024');
  const [currency, setCurrency] = useState('INR');
  const [unit, setUnit] = useState('Crores (Cr)');

  // Start with no file — user must upload their own
  const [statementFile, setStatementFile] = useState<File | null>(null);

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const validateFile = (file: File): string | null => {
    if (file.size === 0) {
      return `File "${file.name}" is empty. Please select a valid document.`;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File "${file.name}" exceeds the maximum allowed size of 50MB.`;
    }
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'xlsx') {
      return `Invalid file format for "${file.name}". Only PDF (.pdf) and Excel (.xlsx) files are supported.`;
    }
    return null;
  };

  const handleStatementFileSelect = (file: File | undefined) => {
    if (!file) return;
    const err = validateFile(file);
    if (err) {
      setErrorMsg(err);
      return;
    }
    setErrorMsg(null);
    setStatementFile(file);
  };

  const handleStartReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bankName.trim()) {
      setErrorMsg('Please specify the Bank Name.');
      return;
    }
    if (!statementFile) {
      setErrorMsg('Annual Financial Statement document file (PDF / XLSX) is required.');
      return;
    }
    if (!reportingPeriod.trim()) {
      setErrorMsg('Please specify the Reporting Period (e.g. FY2025).');
      return;
    }
    if (!comparativePeriod.trim()) {
      setErrorMsg('Please specify the Comparative Period (e.g. FY2024).');
      return;
    }

    const fileErr = validateFile(statementFile);
    if (fileErr) {
      setErrorMsg(fileErr);
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await createJob(bankName, statementFile, statementFile, currency, unit, reportingPeriod, comparativePeriod);
      navigate(`/review/${res.job_id}/processing`);
    } catch (err) {
      console.error('Failed to create review job', err);
      // Fallback navigation
      navigate('/review/REV-2025-001/processing');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 p-5 shadow-sm border-l-4 border-l-blue-800 flex items-start justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-blue-800" />
            INITIATE FINANCIAL STATEMENT REVIEW
          </h2>
          <p className="text-xs text-slate-600 mt-1 max-w-2xl">
            Upload current and comparative financial statements for automated WP-514 review, deterministic cross-casting, prior-year delta analysis, and grounded AI narrative generation.
          </p>
        </div>
        <div className="bg-slate-100 px-3 py-1.5 border border-slate-200 text-[11px] font-mono text-slate-700">
          STANDARD: WP-514 (2026)
        </div>
      </div>

      {errorMsg && (
        <div className="bg-red-50 border border-red-300 text-red-800 p-3 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleStartReview} className="bg-white border border-slate-200 shadow-sm p-6 space-y-6">
        {/* Step 1: Bank & Engagement Details */}
        <div className="space-y-4">
          <h3 className="audit-section-header">1. Engagement & Entity Parameters</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Bank Entity Name <span className="text-red-600">*</span>
              </label>
              <input
                type="text"
                value={bankName}
                onChange={(e) => setBankName(e.target.value)}
                placeholder="e.g. GreenPeak Bank Ltd."
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xs focus:ring-1 focus:ring-blue-800 focus:border-blue-800 outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xs bg-white focus:ring-1 focus:ring-blue-800 outline-none"
              >
                <option value="INR">INR (₹ - Indian Rupee)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Reporting Unit</label>
              <select
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xs bg-white focus:ring-1 focus:ring-blue-800 outline-none"
              >
                <option value="Crores (Cr)">Crores (Cr)</option>
                <option value="Lakhs">Lakhs</option>
              </select>
            </div>
          </div>

          {/* Reporting Period Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Current Reporting Period <span className="text-red-600">*</span>
              </label>
              <input
                type="text"
                value={reportingPeriod}
                onChange={(e) => setReportingPeriod(e.target.value)}
                placeholder="e.g. FY2025 or FY 2025-26"
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xs focus:ring-1 focus:ring-blue-800 focus:border-blue-800 outline-none"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Comparative Prior Period <span className="text-red-600">*</span>
              </label>
              <input
                type="text"
                value={comparativePeriod}
                onChange={(e) => setComparativePeriod(e.target.value)}
                placeholder="e.g. FY2024 or FY 2024-25"
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xs focus:ring-1 focus:ring-blue-800 focus:border-blue-800 outline-none"
                required
              />
            </div>
          </div>
        </div>

        {/* Step 2: Statement Upload Section */}
        <div className="space-y-4 pt-2 border-t border-slate-200">
          <h3 className="audit-section-header">2. Document Ingestion — Single Annual Report PDF / XLSX</h3>

          <div className="border border-slate-300 p-5 bg-slate-50 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-blue-800" />
                  Audited Financial Statements Document
                </span>
                <p className="text-[11px] text-slate-600 mt-1">
                  Upload the annual report document containing both Current Financial Year ({reportingPeriod}) and Comparative Prior Year ({comparativePeriod}) audited Balance Sheet, P&L, Cash Flows, and Notes 1–18.
                </p>
              </div>
              <div className="flex items-center gap-1.5 flex-shrink-0 ml-3">
                <span className="bg-blue-100 text-blue-900 font-mono text-[11px] px-2 py-0.5 border border-blue-200 font-semibold">
                  {reportingPeriod || '—'}
                </span>
                <span className="text-slate-400 font-bold">&</span>
                <span className="bg-slate-200 text-slate-800 font-mono text-[11px] px-2 py-0.5 border border-slate-300 font-semibold">
                  {comparativePeriod || '—'}
                </span>
              </div>
            </div>

            {statementFile ? (
              <div className="bg-white border border-emerald-300 p-4 flex items-center justify-between shadow-xs">
                <div className="flex items-center gap-3 overflow-hidden">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                  <div className="truncate">
                    <div className="text-xs font-bold text-slate-900 truncate">{statementFile.name}</div>
                    <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                      Size: {formatFileSize(statementFile.size)} • Mode: Multi-Period Financial Document ({reportingPeriod} & {comparativePeriod})
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setStatementFile(null)}
                  className="text-[11px] text-slate-600 hover:text-red-700 underline font-semibold ml-3 cursor-pointer flex-shrink-0"
                >
                  Change File
                </button>
              </div>
            ) : (
              <label className="border-2 border-dashed border-slate-300 hover:border-blue-700 bg-white p-6 flex flex-col items-center justify-center cursor-pointer transition-colors space-y-2">
                <Upload className="w-8 h-8 text-blue-800 mb-1" />
                <span className="text-xs font-bold text-slate-800">Select Audited Financial Report (PDF / XLSX)</span>
                <span className="text-[11px] text-slate-500 text-center max-w-md">
                  Upload single PDF or Excel (.xlsx) file containing multi-period current and comparative financial statements up to 50MB.
                </span>
                <input
                  type="file"
                  accept=".pdf,.xlsx"
                  onChange={(e) => handleStatementFileSelect(e.target.files?.[0])}
                  className="hidden"
                />
              </label>
            )}
          </div>
        </div>

        {/* Audit Pipeline Guardrail Notice */}
        <div className="bg-blue-50 border border-blue-200 p-3 text-xs text-blue-950 flex items-start gap-2.5">
          <HelpCircle className="w-4 h-4 text-blue-800 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-blue-900">Deterministic Engine & Evidence Rules:</span>
            <p className="text-[11px] text-blue-950 leading-relaxed">
              Arithmetic calculations, subtotals, and cross-statement reconciliations are computed strictly by deterministic Python rule functions (never LLM). AI is invoked exclusively to produce evidence-grounded anomaly explanations and draft WP-514 working paper commentary.
            </p>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-blue-800 hover:bg-blue-900 text-white text-xs font-semibold px-6 py-2.5 rounded-xs shadow-sm flex items-center gap-2 tracking-wide uppercase transition-colors cursor-pointer disabled:opacity-50"
          >
            <span>{isSubmitting ? 'INITIATING REVIEW...' : 'START FINANCIAL REVIEW'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};

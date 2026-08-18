import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useParams, useLocation } from 'react-router-dom';
import {
  FilePlus,
  LayoutDashboard,
  BarChart3,
  AlertCircle,
  FileCheck2,
  FileSpreadsheet,
  Building2,
  ShieldAlert,
  Clock
} from 'lucide-react';
import { ReviewMetadata } from '../../types/review';
import { fetchReview } from '../../services/api';
import { AuditLensLogo } from '../common/AuditLensLogo';

interface AppShellProps {
  metadata?: ReviewMetadata;
}

export const AppShell: React.FC<AppShellProps> = ({ metadata: propMetadata }) => {
  const { jobId } = useParams();
  const location = useLocation();
  const [metadata, setMetadata] = useState<ReviewMetadata | undefined>(propMetadata);
  const [firstFindingId, setFirstFindingId] = useState<string>('F-002');

  // Fetch review metadata and findings from API whenever jobId changes,
  // so the header bar always reflects the current job's bank name, periods, and evidence ID
  useEffect(() => {
    if (!jobId) {
      setMetadata(undefined);
      return;
    }
    fetchReview(jobId)
      .then((res) => {
        if (res?.review_metadata) {
          setMetadata(res.review_metadata);
        }
        if (res?.findings && res.findings.length > 0) {
          setFirstFindingId(res.findings[0].finding_id);
        }
      })
      .catch(() => {
        // Silently fall back to defaults
      });
  }, [jobId]);

  // Also accept prop overrides
  useEffect(() => {
    if (propMetadata) setMetadata(propMetadata);
  }, [propMetadata]);

  const isNewReviewPage = location.pathname === '/review/new';
  const effectiveJobId = jobId || 'REV-2025-001';

  const navItems = [
    { path: `/review/new`, label: 'New Review', icon: FilePlus },
    { path: `/review/${effectiveJobId}/overview`, label: 'Overview', icon: LayoutDashboard },
    { path: `/review/${effectiveJobId}/analysis`, label: 'Financial Analytics', icon: BarChart3 },
    { path: `/review/${effectiveJobId}/findings`, label: 'Findings Workspace', icon: AlertCircle },
    { path: `/review/${effectiveJobId}/evidence/${firstFindingId}`, label: 'Evidence Viewer', icon: FileCheck2 },
    { path: `/review/${effectiveJobId}/wp514`, label: 'WP-514 Working Paper', icon: FileSpreadsheet },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-100 font-sans text-slate-900">
      {/* Top Professional Header */}
      <header className="bg-slate-900 text-white border-b border-slate-800 px-4 py-2 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <AuditLensLogo size="sm" />
          <div className="h-4 w-[1px] bg-slate-700 hidden sm:block" />
          <h1 className="text-xs sm:text-sm font-semibold tracking-tight text-slate-100 hidden md:block">
            BANKING FINANCIAL STATEMENT REVIEW AUTOMATION
          </h1>
          <span className="bg-slate-800 text-slate-300 text-[10px] uppercase font-mono px-2 py-0.5 border border-slate-700 hidden lg:inline-block">
            WP-514 ENGINE
          </span>
        </div>

        {/* Bank & Active Review Meta */}
        {!isNewReviewPage && jobId && (
          <div className="flex items-center gap-4 text-xs text-slate-300">
            <div className="flex items-center gap-1.5 bg-slate-800 px-2.5 py-1 border border-slate-700">
              <span className="text-slate-400 font-medium">Bank:</span>
              <span className="font-semibold text-white">{metadata?.bank_name || '—'}</span>
              <span className="text-slate-400 font-mono">({metadata?.reporting_period || '—'} vs {metadata?.comparative_period || '—'})</span>
            </div>

            <div className="flex items-center gap-1.5 bg-slate-800 px-2.5 py-1 border border-slate-700">
              <span className="text-slate-400 font-medium">Job ID:</span>
              <span className="font-mono text-slate-200">{jobId}</span>
            </div>

            <div className="bg-red-900/80 border border-red-700 text-red-200 px-2.5 py-1 font-bold text-[11px] uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>{metadata?.overall_status || 'EXCEPTIONS FOUND'}</span>
            </div>
          </div>
        )}
      </header>

      {/* Main Layout Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar Navigation */}
        <aside className="w-64 bg-slate-900 text-slate-300 border-r border-slate-800 flex flex-col flex-shrink-0">
          <div className="p-3 border-b border-slate-800">
            <div className="text-[10px] uppercase tracking-wider font-bold text-slate-400">
              Audit Navigation
            </div>
          </div>

          <nav className="p-2 space-y-1 flex-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isEvidenceItem = item.path.includes('/evidence/');
              const isEvidenceActive = location.pathname.includes('/evidence/');
              const isActive = isEvidenceItem
                ? isEvidenceActive
                : item.path === `/review/new`
                ? location.pathname === `/review/new`
                : location.pathname.includes(item.path.split('/')[3]);

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={
                    `flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded-xs transition-colors ${
                      isActive
                        ? 'bg-blue-800 text-white font-semibold border-l-2 border-blue-400'
                        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 text-slate-400 group-hover:text-white" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* Audit Working Paper Footer Info */}
          <div className="p-3 border-t border-slate-800 bg-slate-950 text-[11px] text-slate-400 space-y-1">
            <div className="flex items-center justify-between">
              <span>Standard:</span>
              <span className="font-semibold text-slate-300">WP-514 Working Paper</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Mode:</span>
              <span className="font-mono text-emerald-400 text-[10px]">Deterministic + Grounded AI</span>
            </div>
            <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-900 flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-400" />
              <span>Review Date: {metadata?.review_date || new Date().toISOString().split('T')[0]}</span>
            </div>
          </div>
        </aside>

        {/* Page Content Container */}
        <main className="flex-1 overflow-y-auto p-5 bg-slate-100">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

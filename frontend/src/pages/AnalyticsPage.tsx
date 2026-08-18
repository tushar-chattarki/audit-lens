import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { BarChart3, TrendingUp, AlertTriangle, Layers, DollarSign } from 'lucide-react';
import { fetchReview } from '../services/api';
import { ReviewResponse } from '../types/review';

export const AnalyticsPage: React.FC = () => {
  const { jobId = 'REV-2025-001' } = useParams();
  const [data, setData] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReview(jobId).then((res) => {
      setData(res);
      setLoading(false);
    });
  }, [jobId]);

  if (loading || !data) {
    return <div className="p-8 text-center text-xs text-slate-500 font-mono">Loading financial analytics...</div>;
  }

  const { canonical_metrics, summary_kpis, review_metadata } = data;

  // Dynamic period labels from the actual job metadata
  const currentPeriod = review_metadata.reporting_period || 'Current';
  const priorPeriod = review_metadata.comparative_period || 'Prior';
  const currencySymbol = review_metadata.currency === 'USD' ? '$' : review_metadata.currency === 'EUR' ? '€' : review_metadata.currency === 'GBP' ? '£' : '₹';
  const unitLabel = review_metadata.unit || 'Cr';
  // Short unit for display (e.g. "Crores (Cr)" -> "Cr", "Lakhs" -> "Lakhs")
  const unitShort = unitLabel.includes('(') ? unitLabel.split('(')[1].replace(')', '') : unitLabel;

  // Build comparison data from actual canonical_metrics — only include metrics that exist
  const comparisonItems: { metric: string; current: number; prior: number }[] = [];
  if (canonical_metrics.net_income) {
    comparisonItems.push({ metric: 'Net Income', current: canonical_metrics.net_income.current, prior: canonical_metrics.net_income.prior });
  }
  if (canonical_metrics.net_interest_income) {
    comparisonItems.push({ metric: 'Net Interest Income', current: canonical_metrics.net_interest_income.current, prior: canonical_metrics.net_interest_income.prior });
  }
  if (canonical_metrics.other_income) {
    comparisonItems.push({ metric: 'Other Income', current: canonical_metrics.other_income.current, prior: canonical_metrics.other_income.prior });
  }
  if (canonical_metrics.total_assets) {
    comparisonItems.push({ metric: 'Total Assets', current: canonical_metrics.total_assets.current, prior: canonical_metrics.total_assets.prior });
  }
  if (canonical_metrics.bs_cash) {
    comparisonItems.push({ metric: 'BS Cash', current: canonical_metrics.bs_cash.current, prior: canonical_metrics.bs_cash.prior });
  }

  // If no canonical_metrics exist at all, show a placeholder message
  const hasMetrics = comparisonItems.length > 0;

  // Chart A data with dynamic keys
  const comparisonData = comparisonItems.map(item => ({
    metric: item.metric,
    [currentPeriod]: item.current,
    [priorPeriod]: item.prior,
  }));

  // Chart B: YoY Movement % — only include metrics with change_pct data
  const movementData: { name: string; pct: number; color: string }[] = [];
  const movementColors = ['#b91c1c', '#1e3a8a', '#2563eb', '#475569', '#64748b', '#0d9488'];
  const metricsForMovement = [
    { key: 'other_income', label: 'Other Income' },
    { key: 'net_income', label: 'Net Income' },
    { key: 'bs_cash', label: 'BS Cash' },
    { key: 'total_assets', label: 'Total Assets' },
    { key: 'net_interest_income', label: 'Net Interest Income' },
  ];
  metricsForMovement.forEach((m, idx) => {
    const val = (canonical_metrics as any)[m.key];
    if (val && val.change_pct !== undefined && val.change_pct !== null) {
      movementData.push({ name: m.label, pct: val.change_pct, color: movementColors[idx % movementColors.length] });
    }
  });
  // Sort by absolute percentage descending
  movementData.sort((a, b) => Math.abs(b.pct) - Math.abs(a.pct));

  // Chart C: Severity Breakdown — from actual KPIs
  const severityData = [
    { name: 'High Severity', value: summary_kpis.high_severity, color: '#b91c1c' },
    { name: 'Medium Severity', value: summary_kpis.medium_severity, color: '#d97706' },
    { name: 'Low Severity', value: summary_kpis.low_severity, color: '#475569' },
  ];

  // Chart F: Cash Reconciliation — dynamic from canonical_metrics
  const bsCash = canonical_metrics.bs_cash?.current;
  const note12Cash = canonical_metrics.note12_cash?.current;
  const hasCashRecon = bsCash !== undefined && note12Cash !== undefined;
  const cashVariance = hasCashRecon ? Math.abs(bsCash - note12Cash) : 0;

  const cashReconciliationData = hasCashRecon ? [
    {
      category: 'Cash & Equivalents',
      'Balance Sheet': bsCash,
      'Note 12 / Cash Flow': note12Cash,
    },
  ] : [];

  // Dynamic Y-axis domain for cash recon chart
  const cashMin = hasCashRecon ? Math.floor(Math.min(bsCash, note12Cash) * 0.9) : 0;
  const cashMax = hasCashRecon ? Math.ceil(Math.max(bsCash, note12Cash) * 1.1) : 100;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 p-4 shadow-sm flex items-center justify-between border-l-4 border-l-blue-900">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-900" />
            FINANCIAL ANALYTICS & AUDIT CHARTS
          </h2>
          <p className="text-xs text-slate-600 mt-0.5">
            Deterministic metric visualizations, YoY percentage movements, and cross-statement variance breakdowns.
          </p>
        </div>
        <div className="text-xs font-mono bg-slate-100 px-3 py-1 border border-slate-300">
          BANK: {review_metadata.bank_name}
        </div>
      </div>

      {!hasMetrics && (
        <div className="bg-amber-50 border border-amber-300 p-4 text-xs text-amber-900">
          <strong>Note:</strong> No canonical financial metrics are available for this dataset. Charts will display once the math engine processes the uploaded financial statements.
        </div>
      )}

      {/* Grid Row 1: Comparison & YoY Movement */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart A: Current vs Prior Year Comparison */}
        <div className="bg-white border border-slate-200 p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-900" />
              A. Current vs Prior Year Financial Figures ({currencySymbol} {unitShort})
            </h3>
            <span className="text-[10px] font-mono text-slate-500">Grouped Bar</span>
          </div>

          <div className="h-64 w-full">
            {comparisonData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="metric" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(val: number) => [`${currencySymbol}${val.toLocaleString()} ${unitShort}`, '']} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey={currentPeriod} fill="#1e3a8a" name={`${currentPeriod} (Current)`} />
                  <Bar dataKey={priorPeriod} fill="#94a3b8" name={`${priorPeriod} (Prior)`} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400 font-mono">No comparison data available</div>
            )}
          </div>
        </div>

        {/* Chart B: YoY Percentage Movement */}
        <div className="bg-white border border-slate-200 p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-red-700" />
              B. YoY Percentage Movement Analysis (%)
            </h3>
            <span className="text-[10px] font-mono text-slate-500">Horizontal Bar</span>
          </div>

          <div className="h-64 w-full">
            {movementData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={movementData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" tick={{ fontSize: 11 }} unit="%" />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={120} />
                  <Tooltip formatter={(val: number) => [`${val > 0 ? '+' : ''}${val}%`, 'YoY Movement']} />
                  <Bar dataKey="pct" fill="#b91c1c" name="YoY % Change">
                    {movementData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400 font-mono">No YoY movement data available</div>
            )}
          </div>
        </div>
      </div>

      {/* Grid Row 2: Cash Reconciliation Visual & Severity Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart F & E: Cash Reconciliation Variance */}
        <div className="bg-white border border-slate-200 p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-amber-700" />
              F. Cash Reconciliation Variance (BS vs Note 12)
            </h3>
            {hasCashRecon && cashVariance > 0 && (
              <span className="bg-red-100 text-red-800 text-[10px] font-bold px-2 py-0.5 border border-red-300">
                DISCREPANCY: {currencySymbol}{cashVariance.toLocaleString()} {unitShort}
              </span>
            )}
            {hasCashRecon && cashVariance === 0 && (
              <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 border border-emerald-300">
                RECONCILED ✓
              </span>
            )}
          </div>

          <div className="h-56 w-full">
            {hasCashRecon ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={cashReconciliationData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} domain={[cashMin, cashMax]} />
                  <Tooltip formatter={(val: number) => [`${currencySymbol}${val.toLocaleString()} ${unitShort}`, '']} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="Balance Sheet" fill="#1e3a8a" />
                  <Bar dataKey="Note 12 / Cash Flow" fill="#d97706" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400 font-mono">No cash reconciliation data available</div>
            )}
          </div>

          {hasCashRecon && (
            <div className={`${cashVariance > 0 ? 'bg-amber-50 border-amber-200 text-amber-900' : 'bg-emerald-50 border-emerald-200 text-emerald-900'} border p-2.5 text-xs flex items-center justify-between`}>
              <span>Balance Sheet: <strong>{currencySymbol}{bsCash.toLocaleString()} {unitShort}</strong> vs Note 12: <strong>{currencySymbol}{note12Cash.toLocaleString()} {unitShort}</strong></span>
              {cashVariance > 0 ? (
                <span className="font-bold text-red-700 font-mono">Unallocated Variance: {currencySymbol}{cashVariance.toLocaleString()} {unitShort}</span>
              ) : (
                <span className="font-bold text-emerald-700 font-mono">Fully Reconciled</span>
              )}
            </div>
          )}
        </div>

        {/* Chart C: Exception Severity Distribution */}
        <div className="bg-white border border-slate-200 p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-700" />
              C. Exception Severity Breakdown
            </h3>
            <span className="text-[10px] font-mono text-slate-500">Distribution</span>
          </div>

          <div className="h-56 w-full flex items-center justify-center">
            {severityData.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityData.filter(d => d.value > 0)}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {severityData.filter(d => d.value > 0).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-emerald-600 font-semibold">No exceptions found — all checks passed ✓</div>
            )}
          </div>

          <div className="flex items-center justify-center gap-4 text-xs font-semibold text-slate-700 pt-1">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 bg-red-700" />
              <span>High ({summary_kpis.high_severity})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 bg-amber-600" />
              <span>Medium ({summary_kpis.medium_severity})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 bg-slate-600" />
              <span>Low ({summary_kpis.low_severity})</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

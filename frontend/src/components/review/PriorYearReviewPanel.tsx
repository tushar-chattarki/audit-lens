import React from 'react';
import { TrendingUp, AlertTriangle } from 'lucide-react';
import { WP514Section5PriorYear } from '../../types/review';

interface PriorYearReviewPanelProps {
  priorYearChecks: WP514Section5PriorYear[];
}

export const PriorYearReviewPanel: React.FC<PriorYearReviewPanelProps> = ({ priorYearChecks }) => {
  return (
    <div className="bg-white border border-slate-200 shadow-sm p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-slate-200 pb-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-blue-900" />
          Prior-Year Review (YoY Delta Threshold Analysis)
        </h3>
        <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 border border-slate-300">
          WP-514 SECTION 5
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="audit-table">
          <thead>
            <tr>
              <th>Statement</th>
              <th>Line Item</th>
              <th className="text-right">Current Year</th>
              <th className="text-right">Prior Year</th>
              <th className="text-right">Abs Change</th>
              <th className="text-right">% Change</th>
              <th>Review Threshold</th>
              <th>Flag Reason</th>
              <th>Source Ref</th>
            </tr>
          </thead>
          <tbody>
            {priorYearChecks.map((py, idx) => (
              <tr key={idx} className={py.flag ? 'bg-amber-50/50' : ''}>
                <td className="text-slate-800">{py.statement}</td>
                <td className="font-semibold text-slate-900">{py.line_item}</td>
                <td className="text-right font-mono">₹{py.current_year_value.toLocaleString()} Cr</td>
                <td className="text-right font-mono text-slate-600">₹{py.prior_year_value.toLocaleString()} Cr</td>
                <td className="text-right font-mono font-bold text-slate-900">₹{py.absolute_change.toLocaleString()} Cr</td>
                <td className="text-right font-mono font-bold text-red-700">+{py.percentage_change}%</td>
                <td className="font-mono text-[10px] text-slate-700">{py.review_threshold}</td>
                <td className="text-slate-800 text-xs">{py.reason_for_flag}</td>
                <td className="font-mono text-[10px] text-slate-500">{py.source_reference}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

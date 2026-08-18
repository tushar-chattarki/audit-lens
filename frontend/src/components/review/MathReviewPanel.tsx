import React from 'react';
import { Calculator, CheckCircle2, AlertOctagon } from 'lucide-react';
import { WP514Section4MathCheck } from '../../types/review';
import { StatusBadge } from '../common/StatusBadge';

interface MathReviewPanelProps {
  mathChecks: WP514Section4MathCheck[];
}

export const MathReviewPanel: React.FC<MathReviewPanelProps> = ({ mathChecks }) => {
  return (
    <div className="bg-white border border-slate-200 shadow-sm p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-slate-200 pb-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
          <Calculator className="w-4 h-4 text-blue-900" />
          Mathematical Review (Deterministic Engine Checks)
        </h3>
        <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 border border-slate-300">
          WP-514 SECTION 4
        </span>
      </div>

      <div className="overflow-x-auto">
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
              <th className="text-center">Status</th>
            </tr>
          </thead>
          <tbody>
            {mathChecks.map((mc) => (
              <tr key={mc.check_id}>
                <td className="font-mono font-bold text-slate-900">{mc.check_id}</td>
                <td className="text-slate-800">{mc.statement}</td>
                <td className="font-semibold text-slate-900">{mc.check_description}</td>
                <td className="font-mono text-[11px] text-slate-600">{mc.formula_rule}</td>
                <td className="text-right font-mono">₹{mc.reported_result.toLocaleString()} Cr</td>
                <td className="text-right font-mono">₹{mc.calculated_result.toLocaleString()} Cr</td>
                <td className="text-right font-mono font-bold text-red-700">
                  {typeof mc.variance === 'number'
                    ? mc.variance === 0
                      ? '₹0 Cr'
                      : `₹${mc.variance.toLocaleString()} Cr`
                    : String(mc.variance)}
                </td>
                <td className="text-center">
                  <StatusBadge status={mc.status} size="sm" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

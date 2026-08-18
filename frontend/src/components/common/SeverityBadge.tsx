import React from 'react';
import { FindingSeverity } from '../../types/review';

interface SeverityBadgeProps {
  severity: FindingSeverity | string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity }) => {
  const normalized = String(severity).toLowerCase();

  let styles = 'bg-slate-100 text-slate-700 border-slate-300';
  let label = 'LOW';

  if (normalized === 'high' || normalized === 'critical') {
    styles = 'bg-red-100 text-red-900 border-red-300 font-bold';
    label = 'HIGH';
  } else if (normalized === 'medium') {
    styles = 'bg-amber-100 text-amber-900 border-amber-300 font-medium';
    label = 'MEDIUM';
  } else if (normalized === 'low') {
    styles = 'bg-slate-100 text-slate-700 border-slate-300 font-normal';
    label = 'LOW';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 border text-[11px] uppercase tracking-wider rounded-xs ${styles}`}>
      {label}
    </span>
  );
};

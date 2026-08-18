import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, MinusCircle } from 'lucide-react';
import { FindingStatus } from '../../types/review';

interface StatusBadgeProps {
  status: FindingStatus | 'PASS' | 'EXCEPTION' | 'WARNING' | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = String(status).toLowerCase();

  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-300';
  let Icon = MinusCircle;
  let label = 'NOT CHECKED';

  if (normalized === 'pass' || normalized === 'passed') {
    colorClasses = 'bg-emerald-50 text-emerald-800 border-emerald-300 font-semibold';
    Icon = CheckCircle2;
    label = 'PASS';
  } else if (normalized === 'exception' || normalized === 'fail' || normalized === 'failed') {
    colorClasses = 'bg-red-50 text-red-800 border-red-300 font-semibold';
    Icon = XCircle;
    label = 'EXCEPTION';
  } else if (normalized === 'warning' || normalized === 'flagged' || normalized === 'unusual') {
    colorClasses = 'bg-amber-50 text-amber-800 border-amber-300 font-semibold';
    Icon = AlertTriangle;
    label = normalized === 'unusual' ? 'UNUSUAL' : 'WARNING';
  } else if (normalized === 'not_applicable' || normalized === 'na' || normalized === 'review') {
    colorClasses = 'bg-slate-100 text-slate-600 border-slate-300';
    Icon = MinusCircle;
    label = normalized === 'review' ? 'REVIEW' : 'NOT CHECKED';
  }

  const py = size === 'sm' ? 'py-0.5 px-2 text-[10px]' : 'py-1 px-2.5 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 border rounded-sm tracking-wide ${py} ${colorClasses}`}>
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      <span>{label}</span>
    </span>
  );
};

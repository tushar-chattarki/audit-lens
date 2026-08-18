import React, { ReactNode } from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  badge?: ReactNode;
  borderLeftColor?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  badge,
  borderLeftColor = 'border-slate-300',
}) => {
  return (
    <div className={`bg-white border border-slate-200 border-l-4 ${borderLeftColor} p-3.5 shadow-sm flex flex-col justify-between`}>
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">{title}</span>
        {badge}
      </div>
      <div className="text-2xl font-bold text-slate-900 tracking-tight">{value}</div>
      {subtitle && <div className="text-xs text-slate-500 mt-1 font-medium">{subtitle}</div>}
    </div>
  );
};

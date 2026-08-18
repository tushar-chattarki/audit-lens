import React from 'react';

interface AuditLensLogoProps {
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
}

export const AuditLensLogo: React.FC<AuditLensLogoProps> = ({
  size = 'md',
  showSubtitle = false,
}) => {
  const iconSizes = {
    sm: 'w-6 h-6',
    md: 'w-7 h-7',
    lg: 'w-9 h-9',
  };

  const textSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-lg',
  };

  return (
    <div className="flex items-center gap-2.5 select-none">
      {/* Precision Lens Icon */}
      <div className={`relative flex items-center justify-center ${iconSizes[size]} rounded-md bg-gradient-to-br from-blue-600 via-indigo-600 to-cyan-500 p-1 shadow-sm ring-1 ring-white/20`}>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-full h-full text-white"
        >
          {/* Outer Lens Rim */}
          <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2.2" />
          {/* Inner Optical Reticle / Crosshairs */}
          <circle cx="11" cy="11" r="3.5" stroke="currentColor" strokeWidth="1.6" strokeDasharray="2 1.5" className="opacity-90" />
          <circle cx="11" cy="11" r="1" fill="currentColor" />
          {/* Lens Flare / Glass Reflection Arc */}
          <path d="M7 7a5.5 5.5 0 0 1 7.8 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="opacity-75" />
          {/* Precision Handle / Focus Mount */}
          <line x1="17" y1="17" x2="22" y2="22" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" />
        </svg>
      </div>

      {/* Brand Wordmark */}
      <div className="flex flex-col leading-tight">
        <div className={`flex items-center gap-1 font-extrabold tracking-wider font-sans ${textSizes[size]}`}>
          <span className="text-white">AUDIT</span>
          <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent drop-shadow-xs">
            LENS
          </span>
        </div>
        {showSubtitle && (
          <span className="text-[9px] uppercase tracking-widest font-mono text-slate-400 font-medium">
            Financial Statement Review
          </span>
        )}
      </div>
    </div>
  );
};

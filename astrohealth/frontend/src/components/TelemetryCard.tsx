import React from 'react';
import { LucideIcon } from 'lucide-react';

interface TelemetryCardProps {
  title: string;
  value: string | number;
  unit: string;
  icon: LucideIcon;
  status: 'nominal' | 'attention' | 'urgent' | 'emergency';
  baseline?: string;
  subtext?: string;
  quality?: number;
  isSimulated?: boolean;
}

export const TelemetryCard: React.FC<TelemetryCardProps> = ({
  title,
  value,
  unit,
  icon: Icon,
  status,
  baseline,
  subtext,
  quality,
  isSimulated
}) => {
  const getStatusStyles = () => {
    switch (status) {
      case 'emergency':
        return {
          border: 'border-red-500/50 bg-red-950/20 text-red-400',
          badge: 'bg-red-500/20 text-red-300 border-red-500/30',
          accent: 'text-red-400',
          glow: 'shadow-alert-glow'
        };
      case 'urgent':
        return {
          border: 'border-amber-500/50 bg-amber-950/20 text-amber-400',
          badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
          accent: 'text-amber-400',
          glow: 'shadow-panel'
        };
      case 'attention':
        return {
          border: 'border-cyan-500/40 bg-cyan-950/20 text-cyan-400',
          badge: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
          accent: 'text-cyan-400',
          glow: 'shadow-cyan-glow'
        };
      default:
        return {
          border: 'border-space-800 bg-space-900/60 text-emerald-400',
          badge: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
          accent: 'text-cyan-400',
          glow: 'shadow-panel'
        };
    }
  };

  const styles = getStatusStyles();

  return (
    <div className={`rounded-xl border p-4 transition-all duration-300 backdrop-blur-md ${styles.border} ${styles.glow}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <div className="p-2 rounded-lg bg-space-800/80 border border-space-700">
            <Icon className={`w-4 h-4 ${styles.accent}`} />
          </div>
          <div>
            <h3 className="text-xs font-medium text-slate-300 uppercase tracking-wider">{title}</h3>
            {subtext && <p className="text-[10px] text-slate-500 font-mono">{subtext}</p>}
          </div>
        </div>
        <div className="flex items-center space-x-1.5">
          {isSimulated && (
            <span className="text-[9px] font-mono px-1 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
              SIM
            </span>
          )}
          <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border font-semibold ${styles.badge}`}>
            {status}
          </span>
        </div>
      </div>

      <div className="flex items-baseline space-x-2 mt-2">
        <span className="text-2xl sm:text-3xl font-bold font-mono tracking-tight text-white">
          {value}
        </span>
        <span className="text-xs font-mono text-slate-400 uppercase">{unit}</span>
      </div>

      <div className="mt-3 pt-2.5 border-t border-space-800/80 flex items-center justify-between text-[11px] text-slate-400 font-mono">
        <div>
          {baseline && (
            <span>Base: <span className="text-slate-300">{baseline}</span></span>
          )}
        </div>
        {quality !== undefined && (
          <div className="flex items-center space-x-1">
            <span className="text-slate-500">Quality:</span>
            <span className={quality > 0.85 ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold'}>
              {(quality * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
};


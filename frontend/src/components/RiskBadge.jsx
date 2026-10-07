import React from 'react';
import { AlertOctagon, AlertTriangle, ShieldCheck, Info } from 'lucide-react';

export default function RiskBadge({ level, probability }) {
  const normalizedLevel = (level || 'LOW').toUpperCase();
  const probPercent = probability !== undefined ? Math.round(probability * 100) : null;

  const styles = {
    CRITICAL: {
      bg: 'bg-rose-500/15 border-rose-500/40 text-rose-300',
      icon: <AlertOctagon className="w-4 h-4 text-rose-400 animate-pulse" />,
      dot: 'bg-rose-500 animate-ping',
    },
    HIGH: {
      bg: 'bg-amber-500/15 border-amber-500/40 text-amber-300',
      icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
      dot: 'bg-amber-500',
    },
    MODERATE: {
      bg: 'bg-yellow-500/15 border-yellow-500/40 text-yellow-300',
      icon: <Info className="w-4 h-4 text-yellow-400" />,
      dot: 'bg-yellow-500',
    },
    LOW: {
      bg: 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300',
      icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
      dot: 'bg-emerald-500',
    },
  };

  const current = styles[normalizedLevel] || styles.LOW;

  return (
    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold border ${current.bg} shadow-sm`}>
      <span className="relative flex h-2 w-2">
        <span className={`absolute inline-flex h-full w-full rounded-full ${current.dot} opacity-75`}></span>
        <span className={`relative inline-flex rounded-full h-2 w-2 ${current.dot.replace('animate-ping', '')}`}></span>
      </span>
      {current.icon}
      <span>{normalizedLevel} RISK</span>
      {probPercent !== null && (
        <span className="ml-1 opacity-80 border-l border-current/20 pl-2 font-mono">
          {probPercent}%
        </span>
      )}
    </span>
  );
}

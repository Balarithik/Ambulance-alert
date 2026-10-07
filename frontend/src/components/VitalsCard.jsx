import React from 'react';
import { Heart, Thermometer, Activity, Wind } from 'lucide-react';

export default function VitalsCard({ vitals }) {
  const { heart_rate, temperature, sbp, dbp, respiratory_rate } = vitals || {};

  const getHRColor = (hr) => {
    if (!hr) return 'text-slate-400';
    if (hr > 120 || hr < 50) return 'text-rose-400 font-bold';
    if (hr > 100 || hr < 60) return 'text-amber-400';
    return 'text-emerald-400';
  };

  const getTempColor = (t) => {
    if (!t) return 'text-slate-400';
    if (t >= 38.5 || t < 35.5) return 'text-rose-400 font-bold';
    if (t >= 37.5) return 'text-amber-400';
    return 'text-emerald-400';
  };

  const getBPColor = (s, d) => {
    if (!s || !d) return 'text-slate-400';
    if (s >= 140 || s < 90 || d >= 90 || d < 60) return 'text-rose-400 font-bold';
    if (s >= 130 || d >= 85) return 'text-amber-400';
    return 'text-emerald-400';
  };

  const getRespColor = (rr) => {
    if (!rr) return 'text-slate-400';
    if (rr >= 24 || rr < 10) return 'text-rose-400 font-bold';
    if (rr >= 20) return 'text-amber-400';
    return 'text-emerald-400';
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {/* Heart Rate */}
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
          <Heart className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <div className="text-xs text-slate-400 font-medium">Heart Rate</div>
          <div className={`text-lg font-mono font-semibold ${getHRColor(heart_rate)}`}>
            {heart_rate ? `${Math.round(heart_rate)} bpm` : '--'}
          </div>
        </div>
      </div>

      {/* Temperature */}
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
          <Thermometer className="w-5 h-5" />
        </div>
        <div>
          <div className="text-xs text-slate-400 font-medium">Temperature</div>
          <div className={`text-lg font-mono font-semibold ${getTempColor(temperature)}`}>
            {temperature ? `${Number(temperature).toFixed(1)} °C` : '--'}
          </div>
        </div>
      </div>

      {/* Blood Pressure */}
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <div className="text-xs text-slate-400 font-medium">Blood Pressure</div>
          <div className={`text-lg font-mono font-semibold ${getBPColor(sbp, dbp)}`}>
            {sbp && dbp ? `${Math.round(sbp)}/${Math.round(dbp)}` : '--'}
            <span className="text-xs font-normal text-slate-400 ml-1">mmHg</span>
          </div>
        </div>
      </div>

      {/* Respiratory Rate */}
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-teal-500/10 text-teal-400">
          <Wind className="w-5 h-5" />
        </div>
        <div>
          <div className="text-xs text-slate-400 font-medium">Resp. Rate</div>
          <div className={`text-lg font-mono font-semibold ${getRespColor(respiratory_rate)}`}>
            {respiratory_rate ? `${Math.round(respiratory_rate)} /min` : '--'}
          </div>
        </div>
      </div>
    </div>
  );
}

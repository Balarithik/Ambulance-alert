import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, Ambulance, Building2, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-slate-950 font-bold shadow-md shadow-emerald-500/20">
                <Activity className="w-6 h-6 stroke-[2.5]" />
              </div>
              <div>
                <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
                  LifeSync<span className="text-emerald-400">AI</span>
                </span>
                <span className="block text-[10px] text-slate-400 font-medium -mt-1 tracking-wider uppercase">
                  Ambulance-to-Hospital Care System
                </span>
              </div>
            </Link>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <Link
              to="/ambulance"
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive('/ambulance')
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Ambulance className="w-4 h-4" />
              <span>Ambulance Portal</span>
            </Link>

            <Link
              to="/hospital"
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive('/hospital')
                  ? 'bg-teal-500/10 text-teal-400 border border-teal-500/30'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Building2 className="w-4 h-4" />
              <span>Hospital ER Dashboard</span>
            </Link>

            <Link
              to="/alerts"
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive('/alerts')
                  ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <AlertTriangle className="w-4 h-4" />
              <span>Critical Alerts</span>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

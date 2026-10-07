import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Ambulance, Building2, Cpu, Activity, ArrowRight, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { mlAPI } from '../api';

export default function HomePage() {
  const [mlHealth, setMlHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkMlHealth = async () => {
    setLoading(true);
    try {
      const res = await mlAPI.health();
      setMlHealth(res.data);
    } catch (err) {
      console.error('Failed to connect to ML Engine:', err);
      setMlHealth({ model_loaded: false, error: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkMlHealth();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
      {/* Hero Section */}
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
          <Activity className="w-3.5 h-3.5" />
          <span>ECE Project • LifeSyncAI Monitoring System</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
          Ambulance-to-Hospital <br />
          <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            AI Patient Monitoring & Alert System
          </span>
        </h1>
        <p className="text-slate-400 text-base sm:text-lg">
          Connecting IoT ESP32 ambulance vitals with an ML deterioration model to prepare emergency rooms before patient arrival.
        </p>
      </div>

      {/* System Status Panel */}
      <div className="bg-slate-800/60 border border-slate-700/70 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-slate-700/50 rounded-xl text-emerald-400">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">System Diagnostics & ML Engine Status</h3>
              <p className="text-xs text-slate-400">RandomForest classifier (100 trees, 114 features)</p>
            </div>
          </div>

          <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end">
            {loading ? (
              <div className="flex items-center gap-2 text-slate-400 text-sm">
                <RefreshCw className="w-4 h-4 animate-spin text-teal-400" />
                <span>Checking ML model...</span>
              </div>
            ) : mlHealth?.model_loaded ? (
              <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-lg text-xs font-semibold">
                <CheckCircle className="w-4 h-4" />
                <span>ML Model Active & Loaded</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-rose-400 bg-rose-500/10 border border-rose-500/30 px-3 py-1.5 rounded-lg text-xs font-semibold">
                <AlertCircle className="w-4 h-4" />
                <span>ML Model Offline</span>
              </div>
            )}

            <button
              onClick={checkMlHealth}
              className="p-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
              title="Refresh status"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Role Selection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Ambulance Portal Card */}
        <div className="group relative bg-gradient-to-b from-slate-800/90 to-slate-900 border border-slate-700/80 rounded-2xl p-8 hover:border-emerald-500/50 transition-all duration-300 shadow-xl flex flex-col justify-between">
          <div className="space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:scale-105 transition-transform">
              <Ambulance className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white group-hover:text-emerald-400 transition-colors">
                Ambulance Paramedic Portal
              </h2>
              <p className="text-slate-400 text-sm mt-2 leading-relaxed">
                Log patient details, stream live ESP32 vital signs (Heart Rate & Temp), run instant AI risk prediction, and notify the target hospital.
              </p>
            </div>

            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                <span>ESP32 Wi-Fi Data Stream Proxy</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                <span>Simulated Demo Mode for testing</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                <span>Instant Sepsis/Deterioration AI Risk Analysis</span>
              </li>
            </ul>
          </div>

          <div className="mt-8 pt-6 border-t border-slate-800">
            <Link
              to="/ambulance"
              className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition-all shadow-lg shadow-emerald-500/20"
            >
              <span>Launch Ambulance Portal</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* Hospital ER Dashboard Card */}
        <div className="group relative bg-gradient-to-b from-slate-800/90 to-slate-900 border border-slate-700/80 rounded-2xl p-8 hover:border-teal-500/50 transition-all duration-300 shadow-xl flex flex-col justify-between">
          <div className="space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 group-hover:scale-105 transition-transform">
              <Building2 className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white group-hover:text-teal-400 transition-colors">
                Hospital Emergency Dashboard
              </h2>
              <p className="text-slate-400 text-sm mt-2 leading-relaxed">
                Real-time emergency feed for ER doctors to view incoming critical patients, acknowledge alerts, and track equipment preparation status.
              </p>
            </div>

            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-teal-400" />
                <span>Live Incoming Ambulance Patient Stream</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-teal-400" />
                <span>Doctor Preparation Acknowledgment</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-teal-400" />
                <span>Critical Risk Visual Badging & ETA Tracking</span>
              </li>
            </ul>
          </div>

          <div className="mt-8 pt-6 border-t border-slate-800">
            <Link
              to="/hospital"
              className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold transition-all shadow-lg shadow-teal-500/20"
            >
              <span>Launch Hospital Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

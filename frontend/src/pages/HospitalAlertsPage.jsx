import React, { useState, useEffect } from 'react';
import { hospitalAPI } from '../api';
import RiskBadge from '../components/RiskBadge';
import VitalsCard from '../components/VitalsCard';
import { AlertTriangle, ShieldAlert, RefreshCw, CheckCircle } from 'lucide-react';

export default function HospitalAlertsPage() {
  const [criticalPreps, setCriticalPreps] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchCriticalAlerts = async () => {
    setLoading(true);
    try {
      const res = await hospitalAPI.listPreparations();
      const highOrCritical = res.data.filter((prep) => {
        const risk = prep.latest_prediction?.risk_level || 'LOW';
        return risk === 'CRITICAL' || risk === 'HIGH';
      });
      setCriticalPreps(highOrCritical);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCriticalAlerts();
    const interval = setInterval(fetchCriticalAlerts, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="flex items-center justify-between border-b border-slate-800 pb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400">
            <AlertTriangle className="w-7 h-7 animate-bounce" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Critical & High Risk Patient Alerts</h1>
            <p className="text-xs text-slate-400">Dedicated high-priority triage monitor for trauma & ICU teams</p>
          </div>
        </div>

        <button
          onClick={fetchCriticalAlerts}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Critical Feed</span>
        </button>
      </div>

      {criticalPreps.length === 0 ? (
        <div className="p-12 text-center text-slate-400 space-y-3 bg-slate-800/40 rounded-2xl border border-slate-800">
          <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto" />
          <p className="text-lg font-bold text-slate-200">No Critical or High Risk Patients En Route</p>
          <p className="text-xs text-slate-500">System is monitoring all incoming ambulance feeds.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {criticalPreps.map((prep) => (
            <div
              key={prep.id}
              className="bg-slate-800/80 border border-rose-500/40 rounded-2xl p-6 space-y-4 shadow-2xl relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-2 h-full bg-rose-500"></div>

              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white">
                    {prep.patient_info?.name || 'Emergency Patient'}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    ID: <span className="font-mono text-slate-300">{prep.patient_info?.patient_id}</span> • ETA: <strong className="text-white">{prep.ambulance_info?.eta_minutes || 10} mins</strong>
                  </p>
                </div>
                <RiskBadge
                  level={prep.latest_prediction?.risk_level}
                  probability={prep.latest_prediction?.risk_probability}
                />
              </div>

              <VitalsCard vitals={prep.latest_vitals} />

              <div className="bg-slate-900/90 p-4 rounded-xl border border-slate-700/60 space-y-2 text-xs">
                <div>
                  <span className="text-slate-400 font-semibold">Required Trauma Equipment:</span>
                  <p className="text-rose-300 font-bold text-sm mt-0.5">{prep.required_preparation}</p>
                </div>

                <div>
                  <span className="text-slate-400 font-semibold">Symptoms:</span>
                  <p className="text-slate-300">{prep.patient_info?.symptoms || 'Severe deterioration'}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

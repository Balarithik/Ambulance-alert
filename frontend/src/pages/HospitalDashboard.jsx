import React, { useState, useEffect } from 'react';
import { hospitalAPI } from '../api';
import RiskBadge from '../components/RiskBadge';
import VitalsCard from '../components/VitalsCard';
import { Building2, RefreshCw, CheckCircle, Clock, UserCheck, ChevronRight, Filter, Camera, Eye } from 'lucide-react';

export default function HospitalDashboard() {
  const [preparations, setPreparations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterRisk, setFilterRisk] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');

  // Selected item for detail view / acknowledgment
  const [selectedPrep, setSelectedPrep] = useState(null);
  const [doctorName, setDoctorName] = useState('Dr. Sarah Jenkins');
  const [prepNotes, setPrepNotes] = useState('Reserving ICU Bed 4 & notifying trauma team');
  const [actionLoading, setActionLoading] = useState(false);
  const [modalImage, setModalImage] = useState(null);

  const fetchPreparations = async () => {
    setLoading(true);
    try {
      const res = await hospitalAPI.listPreparations();
      setPreparations(res.data);
    } catch (err) {
      console.error('Failed to load hospital preparations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPreparations();
    const interval = setInterval(fetchPreparations, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAcknowledge = async (prepId) => {
    setActionLoading(true);
    try {
      await hospitalAPI.acknowledge(prepId, {
        acknowledged_by: doctorName,
        notes: prepNotes,
      });
      await fetchPreparations();
      if (selectedPrep?.id === prepId) {
        setSelectedPrep((prev) => prev ? { ...prev, status: 'ACKNOWLEDGED', acknowledged_by: doctorName, notes: prepNotes } : null);
      }
    } catch (err) {
      console.error('Failed to acknowledge:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateStatus = async (prepId, newStatus) => {
    setActionLoading(true);
    try {
      await hospitalAPI.updateStatus(prepId, { status: newStatus });
      await fetchPreparations();
      if (selectedPrep?.id === prepId) {
        setSelectedPrep((prev) => prev ? { ...prev, status: newStatus } : null);
      }
    } catch (err) {
      console.error('Failed to update status:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const getFullImageUrl = (imagePath) => {
    if (!imagePath) return null;
    if (imagePath.startsWith('http')) return imagePath;
    return `http://127.0.0.1:8000${imagePath}`;
  };

  // Filtered list
  const filteredPreparations = preparations.filter((prep) => {
    const risk = prep.latest_prediction?.risk_level || 'LOW';
    if (filterRisk !== 'ALL' && risk !== filterRisk) return false;
    if (filterStatus !== 'ALL' && prep.status !== filterStatus) return false;
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Image Zoom Modal */}
      {modalImage && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 cursor-pointer"
          onClick={() => setModalImage(null)}
        >
          <div className="relative max-w-3xl max-h-[85vh] rounded-2xl overflow-hidden border-2 border-emerald-500/50 shadow-2xl">
            <img src={modalImage} alt="Patient Full View" className="w-full h-full object-contain bg-slate-950" />
            <button
              onClick={() => setModalImage(null)}
              className="absolute top-4 right-4 bg-slate-900/80 text-white p-2 rounded-full hover:bg-slate-800"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-teal-500/10 text-teal-400">
            <Building2 className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Hospital Emergency Room Dashboard</h1>
            <p className="text-xs text-slate-400">Real-time incoming ambulance patient stream & live photo feeds</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchPreparations}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all border border-slate-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Feed</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-800/60 border border-slate-700/70 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-300">Filter Feed:</span>

          <div className="flex flex-wrap gap-1.5">
            {['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'].map((rk) => (
              <button
                key={rk}
                onClick={() => setFilterRisk(rk)}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                  filterRisk === rk
                    ? 'bg-teal-500 text-slate-950 shadow'
                    : 'bg-slate-900 text-slate-400 hover:text-white'
                }`}
              >
                {rk}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-400">Status:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1 text-xs text-white"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="PREPARING">Preparing</option>
            <option value="READY">Ready</option>
          </select>
        </div>
      </div>

      {/* Main Grid: Preparations Cards & Detail View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Cards List */}
        <div className="lg:col-span-2 space-y-4">
          {loading && preparations.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-3 bg-slate-800/40 rounded-2xl border border-slate-800">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-teal-400" />
              <p className="text-sm">Connecting to hospital emergency feed...</p>
            </div>
          ) : filteredPreparations.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-3 bg-slate-800/40 rounded-2xl border border-slate-800">
              <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto" />
              <p className="text-base font-semibold text-slate-200">No active patient alerts matching criteria</p>
              <p className="text-xs text-slate-500">New alerts from paramedics will appear automatically.</p>
            </div>
          ) : (
            filteredPreparations.map((prep) => {
              const pInfo = prep.patient_info || {};
              const vInfo = prep.latest_vitals || {};
              const predInfo = prep.latest_prediction || {};
              const isSelected = selectedPrep?.id === prep.id;
              const photoUrl = getFullImageUrl(pInfo.image);

              return (
                <div
                  key={prep.id}
                  onClick={() => setSelectedPrep(prep)}
                  className={`cursor-pointer bg-slate-800/70 border rounded-2xl p-5 transition-all space-y-4 ${
                    isSelected
                      ? 'border-teal-500 ring-2 ring-teal-500/20 shadow-xl'
                      : 'border-slate-700/80 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-4">
                      {photoUrl ? (
                        <div
                          className="relative group shrink-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            setModalImage(photoUrl);
                          }}
                        >
                          <img
                            src={photoUrl}
                            alt="Patient Webcam"
                            className="w-16 h-16 object-cover rounded-xl border-2 border-emerald-500/50 shadow-md group-hover:opacity-80 transition-opacity"
                          />
                          <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 rounded-xl transition-opacity">
                            <Eye className="w-5 h-5 text-white" />
                          </div>
                        </div>
                      ) : (
                        <div className="w-16 h-16 rounded-xl bg-slate-900 border border-slate-700 flex flex-col items-center justify-center text-slate-500 text-[10px] shrink-0">
                          <Camera className="w-5 h-5 mb-0.5 text-slate-600" />
                          <span>No Photo</span>
                        </div>
                      )}

                      <div>
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-bold text-white">
                            {pInfo.name || 'Emergency Patient'}
                          </span>
                          <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400">
                            {pInfo.patient_id || 'ID Unknown'}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 mt-1">
                          Age: {pInfo.age || '--'} • Gender: {pInfo.gender === 'M' ? 'Male' : pInfo.gender === 'F' ? 'Female' : 'Other'} • Symptoms: {pInfo.symptoms || 'Not listed'}
                        </div>
                      </div>
                    </div>

                    <RiskBadge level={predInfo.risk_level} probability={predInfo.risk_probability} />
                  </div>

                  {/* Vitals snapshot */}
                  <VitalsCard vitals={vInfo} />

                  {/* Footer status & actions */}
                  <div className="pt-3 border-t border-slate-700/60 flex flex-wrap items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-4 text-slate-300">
                      <span className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-teal-400" />
                        <span>ETA: <strong className="text-white">{prep.ambulance_info?.eta_minutes || 10} mins</strong> ({prep.ambulance_info?.ambulance_id})</span>
                      </span>
                      <span className="font-semibold px-2.5 py-0.5 rounded-full bg-slate-900 border border-slate-700 text-slate-300">
                        {prep.status}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {prep.status === 'PENDING' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedPrep(prep);
                            handleAcknowledge(prep.id);
                          }}
                          className="px-3 py-1.5 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold rounded-lg transition-all"
                        >
                          Acknowledge
                        </button>
                      )}
                      <ChevronRight className="w-4 h-4 text-slate-500" />
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right Col: Selected Patient Detail & ER Action Drawer */}
        <div className="space-y-6">
          {selectedPrep ? (
            <div className="bg-slate-800/80 border border-slate-700 rounded-2xl p-6 space-y-6 sticky top-20 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-700 pb-4">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <UserCheck className="w-5 h-5 text-teal-400" />
                  <span>ER Team Response</span>
                </h2>
                <RiskBadge
                  level={selectedPrep.latest_prediction?.risk_level}
                  probability={selectedPrep.latest_prediction?.risk_probability}
                />
              </div>

              {/* Patient Photo Preview Box */}
              {selectedPrep.patient_info?.image && (
                <div className="bg-slate-900/90 border border-slate-700/80 rounded-xl p-3 space-y-2">
                  <div className="flex items-center justify-between text-xs text-emerald-400 font-bold">
                    <span className="flex items-center gap-1">
                      <Camera className="w-3.5 h-3.5" />
                      Live Ambulance Webcam Photo
                    </span>
                    <button
                      onClick={() => setModalImage(getFullImageUrl(selectedPrep.patient_info.image))}
                      className="text-slate-400 hover:text-white flex items-center gap-1 text-[11px]"
                    >
                      <Eye className="w-3 h-3" /> Expand
                    </button>
                  </div>
                  <img
                    src={getFullImageUrl(selectedPrep.patient_info.image)}
                    alt="Patient Live Stream"
                    className="w-full h-44 object-cover rounded-lg border border-slate-700 cursor-pointer hover:opacity-90"
                    onClick={() => setModalImage(getFullImageUrl(selectedPrep.patient_info.image))}
                  />
                </div>
              )}

              {/* Patient info details */}
              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-slate-400 font-semibold block">Patient Name & ID:</span>
                  <span className="text-sm font-bold text-white">
                    {selectedPrep.patient_info?.name} ({selectedPrep.patient_info?.patient_id})
                  </span>
                </div>

                <div>
                  <span className="text-slate-400 font-semibold block">Required Hospital Preparation:</span>
                  <p className="text-amber-300 font-semibold bg-amber-500/10 border border-amber-500/30 p-2.5 rounded-lg mt-1">
                    {selectedPrep.required_preparation || 'Standard Emergency Bed'}
                  </p>
                </div>

                <div>
                  <span className="text-slate-400 font-semibold block">Attender / Paramedic Observation:</span>
                  <p className="text-slate-300 bg-slate-900 p-2.5 rounded-lg mt-1">
                    {selectedPrep.patient_info?.attender_observation || 'None provided.'}
                  </p>
                </div>
              </div>

              {/* Doctor Acknowledgment Action Box */}
              <div className="bg-slate-900/80 border border-slate-700 p-4 rounded-xl space-y-3">
                <h4 className="text-xs font-bold text-teal-400 uppercase tracking-wider">Doctor Acknowledgment</h4>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">Attending Physician</label>
                  <input
                    type="text"
                    value={doctorName}
                    onChange={(e) => setDoctorName(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">ER Preparation Notes</label>
                  <textarea
                    rows="2"
                    value={prepNotes}
                    onChange={(e) => setPrepNotes(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white"
                  ></textarea>
                </div>

                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => handleAcknowledge(selectedPrep.id)}
                    disabled={actionLoading}
                    className="flex-1 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold rounded-lg text-xs transition-all"
                  >
                    Confirm Acknowledgment
                  </button>
                </div>
              </div>

              {/* Status Stepper */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-slate-400">Update Hospital Status:</span>
                <div className="grid grid-cols-3 gap-2">
                  {['PENDING', 'PREPARING', 'READY'].map((st) => (
                    <button
                      key={st}
                      onClick={() => handleUpdateStatus(selectedPrep.id, st)}
                      className={`py-2 text-xs font-bold rounded-lg border transition-all ${
                        selectedPrep.status === st
                          ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                          : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-white'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-slate-800/40 border border-slate-800 rounded-2xl p-8 text-center text-slate-500 text-sm space-y-2">
              <Building2 className="w-8 h-8 mx-auto text-slate-600" />
              <p>Select any patient alert card on the left to view detailed vitals and respond.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

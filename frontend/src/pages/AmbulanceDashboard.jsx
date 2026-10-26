import React, { useState, useEffect, useRef } from 'react';
import { patientAPI, ambulanceAPI, mlAPI, hospitalAPI } from '../api';
import RiskBadge from '../components/RiskBadge';
import VitalsCard from '../components/VitalsCard';
import { Ambulance, Cpu, Send, CheckCircle, AlertTriangle, RefreshCw, UserPlus, Upload, ShieldAlert, Sparkles, Camera, Video, Trash2, Eye } from 'lucide-react';

export default function AmbulanceDashboard() {
  const [patientId, setPatientId] = useState(`P-${Math.floor(1000 + Math.random() * 9000)}`);
  const [name, setName] = useState('');
  const [age, setAge] = useState(45);
  const [gender, setGender] = useState('M');
  const [systolicBp, setSystolicBp] = useState(120);
  const [diastolicBp, setDiastolicBp] = useState(80);
  const [respRate, setRespRate] = useState(18);
  const [symptoms, setSymptoms] = useState('High fever, difficulty breathing');
  const [medicalHistory, setMedicalHistory] = useState('Hypertension');
  const [allergies, setAllergies] = useState('None');
  const [attenderObs, setAttenderObs] = useState('Patient is conscious, sweating heavily');
  
  // Photo & Webcam state
  const [imageFile, setImageFile] = useState(null);
  const [capturedImagePreview, setCapturedImagePreview] = useState(null);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Sensor state
  const [esp32Ip, setEsp32Ip] = useState('10.232.175.180');
  const [heartRate, setHeartRate] = useState(85);
  const [temperature, setTemperature] = useState(37.2);
  const [autoPoll, setAutoPoll] = useState(false);
  const [isDemoMode, setIsDemoMode] = useState(true);
  const [demoScenario, setDemoScenario] = useState('high_risk');

  // Prediction & Hospital Prep state
  const [prediction, setPrediction] = useState(null);
  const [loadingPredict, setLoadingPredict] = useState(false);
  const [reqPrep, setReqPrep] = useState('ICU Bed, Oxygen Support, IV Fluids');
  const [etaMinutes, setEtaMinutes] = useState(12);
  const [sendingToHospital, setSendingToHospital] = useState(false);
  const [sentSuccess, setSentSuccess] = useState(false);

  const [activeAmbulanceId, setActiveAmbulanceId] = useState('AMB-01');
  const [statusMsg, setStatusMsg] = useState('');
  const [statusType, setStatusType] = useState('info'); // info, success, error

  // Start Laptop Webcam Stream
  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setIsCameraOpen(true);
      setStatusMsg('Webcam active. Click "Take Photo Snapshot" to capture patient image.');
      setStatusType('info');
    } catch (err) {
      console.error('Webcam access error:', err);
      setStatusMsg(`Webcam error: ${err.message}. Please check browser camera permissions.`);
      setStatusType('error');
    }
  };

  // Stop Laptop Webcam Stream
  const stopWebcam = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject;
      const tracks = stream.getTracks();
      tracks.forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsCameraOpen(false);
  };

  // Take Snapshot from Laptop Webcam
  const takeSnapshot = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
      setCapturedImagePreview(dataUrl);

      // Convert data URL to File object for multipart form upload
      fetch(dataUrl)
        .then((res) => res.blob())
        .then((blob) => {
          const file = new File([blob], `webcam_patient_${Date.now()}.jpg`, { type: 'image/jpeg' });
          setImageFile(file);
          setStatusMsg('Live photo snapshot captured successfully! Ready to share with Hospital ER.');
          setStatusType('success');
        });

      stopWebcam();
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      setCapturedImagePreview(URL.createObjectURL(file));
      setStatusMsg(`Photo selected: ${file.name}`);
      setStatusType('info');
    }
  };

  const clearCapturedPhoto = () => {
    setImageFile(null);
    setCapturedImagePreview(null);
  };

  // ESP32 Fetch (Django Proxy)
  const handleFetchESP32 = async () => {
    try {
      setStatusMsg('Fetching from ESP32 via backend proxy...');
      const res = await ambulanceAPI.fetchESP32(activeAmbulanceId, {
        esp32_ip: esp32Ip,
        patient_id: patientId,
      });

      if (res.data.esp32_data) {
        const data = res.data.esp32_data;
        if (data.heart_rate !== null && data.heart_rate !== undefined) setHeartRate(data.heart_rate);
        if (data.temperature !== null && data.temperature !== undefined) setTemperature(data.temperature);
        setStatusMsg(`ESP32 data received! Reading ID: ${data.reading_id || 0}`);
        setStatusType('success');
      }
    } catch (err) {
      console.error(err);
      setStatusMsg(`ESP32 fetch failed: ${err.response?.data?.error || err.message}`);
      setStatusType('error');
    }
  };

  // Demo Data Generator
  const handleGenerateDemo = async () => {
    try {
      const res = await ambulanceAPI.generateDemoData({
        scenario: demoScenario,
        patient_id: patientId,
      });

      setHeartRate(res.data.heart_rate);
      setTemperature(res.data.temperature);
      if (demoScenario === 'critical') {
        setSystolicBp(85);
        setDiastolicBp(50);
        setRespRate(28);
      } else if (demoScenario === 'high_risk') {
        setSystolicBp(100);
        setDiastolicBp(60);
        setRespRate(24);
      } else {
        setSystolicBp(120);
        setDiastolicBp(80);
        setRespRate(16);
      }

      setStatusMsg(`[DEMO MODE] Generated simulated vitals (${demoScenario})`);
      setStatusType('info');
    } catch (err) {
      console.error(err);
    }
  };

  // Auto poll interval for ESP32
  useEffect(() => {
    let interval;
    if (autoPoll) {
      interval = setInterval(() => {
        if (isDemoMode) {
          handleGenerateDemo();
        } else {
          handleFetchESP32();
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [autoPoll, isDemoMode, esp32Ip, demoScenario]);

  // Cleanup webcam stream on unmount
  useEffect(() => {
    return () => stopWebcam();
  }, []);

  // Run ML Prediction
  const handleRunPrediction = async () => {
    setLoadingPredict(true);
    setStatusMsg('');
    try {
      // The patient profile is created only when "Notify Hospital" is pressed.
      // Include age/gender so an earlier risk assessment works before that request.
      const vitals = {
        patient_id: patientId.trim(),
        age: Number(age),
        gender,
        heart_rate: Number(heartRate),
        temperature: Number(temperature),
        sbp: Number(systolicBp),
        dbp: Number(diastolicBp),
        respiratory_rate: Number(respRate),
        map_value: (Number(systolicBp) + 2 * Number(diastolicBp)) / 3,
      };

      const res = await mlAPI.predict(vitals);
      setPrediction(res.data);
      setStatusMsg(`Prediction complete: ${res.data.risk_level} Risk (${Math.round(res.data.risk_probability * 100)}%)`);
      setStatusType('success');
    } catch (err) {
      console.error('Prediction failed:', err);
      setStatusMsg(`Prediction failed: ${err.response?.data?.error || err.message}`);
      setStatusType('error');
    } finally {
      setLoadingPredict(false);
    }
  };

  // Register Patient and Send to Hospital
  const handleSendToHospital = async (e) => {
    e.preventDefault();
    setSendingToHospital(true);
    setSentSuccess(false);

    try {
      // 1. Create or update patient with image upload
      const formData = new FormData();
      formData.append('patient_id', patientId);
      formData.append('name', name || 'Emergency Patient');
      formData.append('age', age);
      formData.append('gender', gender);
      formData.append('systolic_bp', systolicBp);
      formData.append('diastolic_bp', diastolicBp);
      formData.append('respiratory_rate', respRate);
      formData.append('symptoms', symptoms);
      formData.append('medical_history', medicalHistory);
      formData.append('allergies', allergies);
      formData.append('attender_observation', attenderObs);
      if (imageFile) {
        formData.append('image', imageFile);
      }

      let patient;
      try {
        const createRes = await patientAPI.create(formData);
        patient = createRes.data;
      } catch (err) {
        // Fallback update if patient ID exists
        const checkRes = await patientAPI.get(patientId);
        patient = checkRes.data;
      }

      // 2. Ensure ambulance exists
      let ambulance;
      try {
        const ambRes = await ambulanceAPI.get(activeAmbulanceId);
        ambulance = ambRes.data;
      } catch (err) {
        const createAmb = await ambulanceAPI.create({
          ambulance_id: activeAmbulanceId,
          driver_name: 'Paramedic Unit 1',
          contact_number: '+19998887777',
          esp32_ip: esp32Ip,
          eta_minutes: etaMinutes,
          status: 'EN_ROUTE',
        });
        ambulance = createAmb.data;
      }

      // 3. Create Sensor Reading
      await patientAPI.addSensorReading({
        patient: patient.id,
        reading_id: Math.floor(Math.random() * 90000) + 10000,
        heart_rate: heartRate,
        temperature: temperature,
        device_id: isDemoMode ? 'DEMO-ESP32-SIMULATED' : 'ESP32-HARDWARE',
      });

      // 4. Send Hospital Preparation alert
      await hospitalAPI.createPreparation({
        patient: patient.id,
        ambulance: ambulance.id,
        required_preparation: reqPrep,
        status: 'PENDING',
      });

      setSentSuccess(true);
      setStatusMsg('Alert, Live Photo & Vitals successfully transmitted to Hospital ER Dashboard!');
      setStatusType('success');
    } catch (err) {
      console.error('Failed to send to hospital:', err);
      setStatusMsg(`Transmission failed: ${err.response?.data ? JSON.stringify(err.response.data) : err.message}`);
      setStatusType('error');
    } finally {
      setSendingToHospital(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <Ambulance className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Ambulance Paramedic Portal</h1>
              <p className="text-xs text-slate-400">Live ESP32 Vitals, Webcam Photo Stream & AI Risk Assessment</p>
            </div>
          </div>
        </div>

        {/* Demo Mode Banner */}
        <div className="flex items-center gap-3 bg-slate-800/80 border border-slate-700 rounded-xl p-3">
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${isDemoMode ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'}`}></span>
            <span className="text-xs font-semibold text-slate-200">
              {isDemoMode ? 'DEMO / SIMULATED MODE' : 'HARDWARE ESP32 MODE'}
            </span>
          </div>

          <button
            type="button"
            onClick={() => setIsDemoMode(!isDemoMode)}
            className="px-3 py-1 text-xs font-bold rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 transition-colors"
          >
            Switch to {isDemoMode ? 'Hardware ESP32' : 'Demo Mode'}
          </button>
        </div>
      </div>

      {statusMsg && (
        <div className={`p-4 rounded-xl border text-sm font-medium flex items-center justify-between ${
          statusType === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' :
          statusType === 'error' ? 'bg-rose-500/10 border-rose-500/30 text-rose-300' :
          'bg-cyan-500/10 border-cyan-500/30 text-cyan-300'
        }`}>
          <span>{statusMsg}</span>
          <button onClick={() => setStatusMsg('')} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Col: Vitals & Sensors */}
        <div className="lg:col-span-2 space-y-6">
          {/* Sensor Panel */}
          <div className="bg-slate-800/60 border border-slate-700/70 rounded-2xl p-6 space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-emerald-400" />
                <h2 className="text-lg font-bold text-white">Live Vitals & Sensor Input</h2>
              </div>
              {isDemoMode && (
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/20 border border-amber-500/40 text-amber-300">
                  DEMO ACTIVE
                </span>
              )}
            </div>

            {/* Hardware vs Demo Controls */}
            {isDemoMode ? (
              <div className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="font-semibold text-slate-300">Select Simulated Patient Scenario:</span>
                  <span className="text-slate-500 font-mono">Sensors: LM35 Temp + HR Sensor</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {['stable', 'increasing_risk', 'high_risk', 'critical'].map((sc) => (
                    <button
                      key={sc}
                      type="button"
                      onClick={() => {
                        setDemoScenario(sc);
                        handleGenerateDemo();
                      }}
                      className={`px-3 py-2 rounded-lg text-xs font-bold capitalize transition-all ${
                        demoScenario === sc
                          ? 'bg-emerald-500 text-slate-950 shadow'
                          : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {sc.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-4 flex flex-col sm:flex-row items-center gap-3">
                <div className="flex-1 w-full">
                  <label className="block text-xs font-semibold text-slate-400 mb-1">ESP32 IP Address</label>
                  <input
                    type="text"
                    value={esp32Ip}
                    onChange={(e) => setEsp32Ip(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono"
                    placeholder="10.232.175.180"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleFetchESP32}
                  className="w-full sm:w-auto mt-5 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-lg text-sm transition-all"
                >
                  Fetch ESP32 Vitals
                </button>
              </div>
            )}

            {/* Vitals Summary Card */}
            <VitalsCard
              vitals={{
                heart_rate: heartRate,
                temperature: temperature,
                sbp: systolicBp,
                dbp: diastolicBp,
                respiratory_rate: respRate,
              }}
            />

            {/* Manual Vitals Adjustments */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Heart Rate (bpm)</label>
                <input
                  type="number"
                  value={heartRate || ''}
                  onChange={(e) => setHeartRate(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Temp (°C)</label>
                <input
                  type="number"
                  step="0.1"
                  value={temperature || ''}
                  onChange={(e) => setTemperature(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Systolic BP</label>
                <input
                  type="number"
                  value={systolicBp || ''}
                  onChange={(e) => setSystolicBp(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Diastolic BP</label>
                <input
                  type="number"
                  value={diastolicBp || ''}
                  onChange={(e) => setDiastolicBp(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Resp Rate (/min)</label>
                <input
                  type="number"
                  value={respRate || ''}
                  onChange={(e) => setRespRate(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white font-mono"
                />
              </div>
            </div>

            {/* AI Risk Run Button */}
            <div className="pt-2">
              <button
                type="button"
                onClick={handleRunPrediction}
                disabled={loadingPredict}
                className="w-full py-3 px-4 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-bold rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
              >
                {loadingPredict ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    <span>Running ML Risk Assessment...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    <span>Run AI Deterioration Assessment</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* AI Risk Prediction Result Box */}
          {prediction && (
            <div className="bg-slate-800/80 border border-slate-700 rounded-2xl p-6 space-y-4 shadow-xl">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-emerald-400" />
                  <span>ML Deterioration Model Output</span>
                </h3>
                <RiskBadge level={prediction.risk_level} probability={prediction.risk_probability} />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-slate-900/80 p-4 rounded-xl border border-slate-700/50">
                <div>
                  <div className="text-xs text-slate-400 font-medium">Risk Score</div>
                  <div className="text-2xl font-bold font-mono text-white">
                    {Math.round(prediction.risk_probability * 100)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400 font-medium">Risk Category</div>
                  <div className="text-lg font-bold text-emerald-400">
                    {prediction.risk_level}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400 font-medium">Deterioration Flag</div>
                  <div className="text-lg font-mono font-semibold text-slate-200">
                    {prediction.prediction === 1 ? 'YES (High Risk)' : 'NO (Normal)'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Patient Details & Live Laptop Webcam Capture Section */}
          <div className="bg-slate-800/60 border border-slate-700/70 rounded-2xl p-6 space-y-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-emerald-400" />
              <span>Patient Profile & Observations</span>
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Patient ID</label>
                <input
                  type="text"
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Patient Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Alex Morgan"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Age & Gender</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    className="w-1/2 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono"
                  />
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="w-1/2 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                  >
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                    <option value="O">Other</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Primary Symptoms</label>
                <textarea
                  rows="2"
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                ></textarea>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Attender Observations</label>
                <textarea
                  rows="2"
                  value={attenderObs}
                  onChange={(e) => setAttenderObs(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                ></textarea>
              </div>
            </div>

            {/* LIVE WEBCAM & PATIENT PHOTO SHARING */}
            <div className="bg-slate-900/80 border border-slate-700/80 rounded-xl p-4 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-emerald-400">
                  <Camera className="w-5 h-5" />
                  <span className="text-sm font-bold text-white">Live Patient Photo (Laptop Webcam)</span>
                </div>
                <span className="text-[11px] text-slate-400">Share live image to Hospital ER</span>
              </div>

              {/* Webcam Viewport */}
              {isCameraOpen ? (
                <div className="space-y-3">
                  <div className="relative rounded-xl overflow-hidden bg-black border-2 border-emerald-500/50">
                    <video ref={videoRef} className="w-full h-56 object-cover" autoPlay playsInline muted />
                    <div className="absolute top-3 left-3 bg-rose-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-white animate-ping"></span>
                      LIVE WEBCAM
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={takeSnapshot}
                      className="flex-1 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-lg text-xs flex items-center justify-center gap-2 shadow"
                    >
                      <Camera className="w-4 h-4" />
                      <span>Take Photo Snapshot</span>
                    </button>
                    <button
                      type="button"
                      onClick={stopWebcam}
                      className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-lg text-xs"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : capturedImagePreview ? (
                <div className="flex items-center gap-4 bg-slate-800 p-3 rounded-xl border border-slate-700">
                  <img
                    src={capturedImagePreview}
                    alt="Captured Patient"
                    className="w-24 h-24 object-cover rounded-lg border border-emerald-500/50"
                  />
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-bold">
                      <CheckCircle className="w-4 h-4" />
                      <span>Live Photo Ready for Hospital ER</span>
                    </div>
                    <p className="text-[11px] text-slate-400">Will be transmitted with emergency alert.</p>

                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={startWebcam}
                        className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold rounded-lg flex items-center gap-1"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                        <span>Retake</span>
                      </button>
                      <button
                        type="button"
                        onClick={clearCapturedPhoto}
                        className="px-3 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-xs font-semibold rounded-lg flex items-center gap-1"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        <span>Remove</span>
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col sm:flex-row gap-3">
                  <button
                    type="button"
                    onClick={startWebcam}
                    className="flex-1 py-3 bg-gradient-to-r from-emerald-500/20 to-teal-500/20 hover:from-emerald-500/30 hover:to-teal-500/30 border border-emerald-500/40 text-emerald-300 font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition-all"
                  >
                    <Video className="w-4 h-4 text-emerald-400" />
                    <span>Capture Photo from Laptop Camera</span>
                  </button>

                  <label className="py-3 px-4 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 font-semibold rounded-xl text-xs flex items-center justify-center gap-2 cursor-pointer transition-all">
                    <Upload className="w-4 h-4 text-slate-400" />
                    <span>Upload Image File</span>
                    <input type="file" accept="image/*" onChange={handleFileUpload} className="hidden" />
                  </label>
                </div>
              )}

              {/* Hidden canvas for capturing frame */}
              <canvas ref={canvasRef} className="hidden" />
            </div>
          </div>
        </div>

        {/* Right Col: Hospital Dispatch */}
        <div className="space-y-6">
          <div className="bg-slate-800/60 border border-slate-700/70 rounded-2xl p-6 space-y-5 sticky top-20 shadow-xl">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Send className="w-5 h-5 text-teal-400" />
              <span>Hospital ER Preparation Alert</span>
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Ambulance ID</label>
                <input
                  type="text"
                  value={activeAmbulanceId}
                  onChange={(e) => setActiveAmbulanceId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Estimated Arrival (ETA)</label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    value={etaMinutes}
                    onChange={(e) => setEtaMinutes(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono"
                  />
                  <span className="text-xs text-slate-400 font-medium">Minutes</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Required Hospital Equipment/Prep</label>
                <textarea
                  rows="3"
                  value={reqPrep}
                  onChange={(e) => setReqPrep(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
                  placeholder="e.g. ICU Bed, Ventilator, Blood Bank Prep"
                ></textarea>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleSendToHospital}
                  disabled={sendingToHospital}
                  className="w-full py-3.5 px-4 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
                >
                  {sendingToHospital ? (
                    <>
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      <span>Transmitting Alert & Photo...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      <span>Notify Hospital ER Immediately</span>
                    </>
                  )}
                </button>
              </div>

              {sentSuccess && (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-400 font-semibold flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 shrink-0" />
                  <span>ER Team notified successfully! Live photo and vitals sent.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

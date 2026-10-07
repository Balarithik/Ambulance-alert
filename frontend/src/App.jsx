import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import AmbulanceDashboard from './pages/AmbulanceDashboard';
import HospitalDashboard from './pages/HospitalDashboard';
import HospitalAlertsPage from './pages/HospitalAlertsPage';

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500 selection:text-slate-950">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/ambulance" element={<AmbulanceDashboard />} />
            <Route path="/hospital" element={<HospitalDashboard />} />
            <Route path="/alerts" element={<HospitalAlertsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

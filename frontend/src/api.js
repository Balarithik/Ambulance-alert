import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const patientAPI = {
  list: () => api.get('/patients/'),
  get: (id) => api.get(`/patients/${id}/`),
  create: (data) => {
    if (data instanceof FormData) {
      return api.post('/patients/', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    }
    return api.post('/patients/', data);
  },
  update: (id, data) => api.put(`/patients/${id}/`, data),
  addSensorReading: (data) => api.post('/patients/readings/', data),
};

export const ambulanceAPI = {
  list: () => api.get('/ambulance/'),
  get: (id) => api.get(`/ambulance/${id}/`),
  create: (data) => api.post('/ambulance/', data),
  fetchESP32: (ambulanceId, payload) => api.post(`/ambulance/${ambulanceId}/fetch_esp32/`, payload),
  checkESP32Status: (ambulanceId, ip) => api.get(`/ambulance/${ambulanceId}/esp32_status/`, { params: { esp32_ip: ip } }),
  generateDemoData: (payload) => api.post('/ambulance/demo/generate/', payload),
};

export const mlAPI = {
  predict: (vitals) => api.post('/ml/predict/', vitals),
  health: () => api.get('/ml/health/'),
  reset: () => api.post('/ml/reset/'),
};

export const hospitalAPI = {
  listPreparations: () => api.get('/hospital/preparations/'),
  getActivePreparations: () => api.get('/hospital/preparations/active/'),
  getHistoryPreparations: () => api.get('/hospital/preparations/history/'),
  createPreparation: (data) => api.post('/hospital/preparations/', data),
  acknowledge: (id, data) => api.post(`/hospital/preparations/${id}/acknowledge/`, data),
  updateStatus: (id, data) => api.post(`/hospital/preparations/${id}/update_status/`, data),
};

export default api;

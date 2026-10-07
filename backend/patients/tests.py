from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Patient, SensorReading


class PatientAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient_data = {
            "patient_id": "P101",
            "name": "John Doe",
            "age": 45,
            "gender": "M",
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "respiratory_rate": 18,
            "symptoms": "Fever, chills",
            "medical_history": "Hypertension",
            "allergies": "Penicillin",
            "attender_observation": "Patient is alert but sweating",
        }

    def test_create_and_get_patient(self):
        # Create patient
        response = self.client.post("/api/patients/", self.patient_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["name"], "John Doe")
        self.assertEqual(response.data["patient_id"], "P101")

        # Get patient list
        response = self.client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Get patient detail
        response = self.client.get("/api/patients/P101/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["patient_id"], "P101")

    def test_sensor_reading_creation(self):
        patient = Patient.objects.create(**self.patient_data)
        sensor_data = {
            "patient": patient.id,
            "reading_id": 5001,
            "heart_rate": 88.5,
            "temperature": 37.8,
            "device_id": "ESP32_01",
        }
        response = self.client.post("/api/patients/readings/", sensor_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["heart_rate"], 88.5)

        # Check latest sensor reading on patient endpoint
        response = self.client.get(f"/api/patients/{patient.patient_id}/")
        self.assertIsNotNone(response.data["latest_sensor_reading"])
        self.assertEqual(response.data["latest_sensor_reading"]["heart_rate"], 88.5)

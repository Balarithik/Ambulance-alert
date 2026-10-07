from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from patients.models import Patient


class MLEngineAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient = Patient.objects.create(
            patient_id="P303",
            name="Test Subject",
            age=50,
            gender="M",
        )

    def test_health_check(self):
        response = self.client.get("/api/ml/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["model_loaded"])
        self.assertIn("risk_thresholds", response.data)

    def test_predict_endpoint(self):
        vitals = {
            "heart_rate": 115,
            "temperature": 38.8,
            "sbp": 90,
            "dbp": 55,
            "respiratory_rate": 28,
            "patient_id": "P303",
        }
        response = self.client.post("/api/ml/predict/", vitals, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("risk_probability", response.data)
        self.assertIn("risk_level", response.data)
        self.assertIn("prediction", response.data)
        self.assertIn("prediction_id", response.data)
        self.assertIn(response.data["risk_level"], ["LOW", "MODERATE", "HIGH", "CRITICAL"])

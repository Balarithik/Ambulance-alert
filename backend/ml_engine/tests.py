from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from patients.models import Patient
from ml_engine.ml_predictor import load_predictor


class MLEngineAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient = Patient.objects.create(
            patient_id="P303", name="Test Subject", age=50, gender="M",
        )

    def test_health_check_reports_real_artifact_readiness(self):
        response = self.client.get("/api/ml/health/")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        self.assertIn("model_loaded", response.data)
        self.assertEqual(bool(response.data["model_loaded"]), response.status_code == status.HTTP_200_OK)
        if not response.data["model_loaded"]:
            self.assertTrue(response.data.get("error"))

    def test_prediction_never_fabricates_low_risk_when_artifacts_are_incompatible(self):
        predictor = load_predictor()
        vitals = {
            "heart_rate": 115, "temperature": 38.8, "sbp": 90, "dbp": 55,
            "respiratory_rate": 28, "patient_id": self.patient.patient_id,
        }
        response = self.client.post("/api/ml/predict/", vitals, format="json")
        if not predictor.is_ready:
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertIn("error", response.data)
            self.assertNotIn("risk_level", response.data)
        else:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("risk_probability", response.data)
            self.assertIn(response.data["risk_level"], ["LOW", "MODERATE", "HIGH", "CRITICAL"])
            self.assertIn("prediction_id", response.data)

    def test_prediction_requires_patient_id_to_isolate_history(self):
        response = self.client.post(
            "/api/ml/predict/",
            {"heart_rate": 90, "temperature": 37.2, "sbp": 120, "dbp": 80, "respiratory_rate": 16},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_prediction_rejects_empty_vital_reading(self):
        response = self.client.post(
            "/api/ml/predict/", {"patient_id": self.patient.patient_id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

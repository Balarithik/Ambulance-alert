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


class MLFeatureContractTestCase(TestCase):
    def test_runtime_feature_schema_excludes_unavailable_labs_and_spo2(self):
        from scripts.feature_engineering import get_feature_columns
        columns = get_feature_columns()
        self.assertIn("age", columns)
        self.assertIn("gender", columns)
        self.assertIn("HR", columns)
        self.assertIn("Temp", columns)
        self.assertIn("MAP", columns)
        self.assertIn("HR_trend", columns)
        self.assertNotIn("O2Sat", columns)
        self.assertNotIn("Lactate", columns)
        self.assertEqual(len(columns), len(set(columns)))

    def test_feature_engineering_uses_past_data_and_stable_order(self):
        import pandas as pd
        from scripts.feature_engineering import engineer_patient_features, get_feature_columns

        first = pd.DataFrame([
            {"ICULOS": 1, "Age": 50, "Gender": 1, "HR": 80, "Temp": 37.0, "SBP": 120, "DBP": 80, "Resp": 16, "SepsisLabel": 0},
            {"ICULOS": 2, "Age": 50, "Gender": 1, "HR": 90, "Temp": 37.2, "SBP": 118, "DBP": 78, "Resp": 18, "SepsisLabel": 0},
            {"ICULOS": 3, "Age": 50, "Gender": 1, "HR": 100, "Temp": 37.5, "SBP": 115, "DBP": 75, "Resp": 20, "SepsisLabel": 1},
        ])
        changed_future = first.copy()
        changed_future.loc[2, "HR"] = 200

        original_features = engineer_patient_features(first)
        changed_features = engineer_patient_features(changed_future)
        columns = get_feature_columns()
        self.assertEqual(list(original_features[columns].columns), columns)
        self.assertEqual(original_features.loc[0, "HR_rolling_mean"], changed_features.loc[0, "HR_rolling_mean"])
        self.assertEqual(original_features.loc[1, "HR_rolling_mean"], changed_features.loc[1, "HR_rolling_mean"])
        self.assertEqual(original_features.loc[0, "gender"], 1.0)

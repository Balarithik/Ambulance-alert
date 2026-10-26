"""Compatibility wrapper around the backend's single runtime predictor.

Use the same predictor implementation for scripts and Django so feature order,
preprocessing, risk bands, and patient-specific histories cannot silently diverge.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class SepsisPredictor:
    def __init__(
        self,
        model_path: str | None = None,
        preprocessor_path: str | None = None,
        feature_columns_path: str | None = None,
        risk_thresholds_path: str | None = None,
        vital_columns: list[str] | None = None,
    ):
        # Explicit paths were accepted by the old script API. The current model
        # contract uses the canonical backend/models directory and validates metadata.
        from ml_engine.ml_predictor import SepsisPredictor as RuntimePredictor
        self.predictor = RuntimePredictor()
        self.default_patient_key = "script-demo"

    @property
    def model(self):
        return self.predictor.model

    @property
    def preprocessor(self):
        return self.predictor.preprocessor

    @property
    def feature_columns(self):
        return self.predictor.feature_columns

    @property
    def history_buffer(self):
        return self.predictor.history_by_patient[self.default_patient_key]

    def add_vital_signs(
        self,
        heart_rate: float | None,
        temperature: float | None,
        sbp: float | None,
        dbp: float | None,
        respiratory_rate: float | None,
        age: float | None = None,
        gender: str | int | float | None = None,
        map_value: float | None = None,
        patient_key: str | None = None,
        **_ignored: Any,
    ) -> dict:
        return self.predictor.add_vital_signs(
            patient_key=patient_key or self.default_patient_key,
            heart_rate=heart_rate,
            temperature=temperature,
            sbp=sbp,
            dbp=dbp,
            respiratory_rate=respiratory_rate,
            age=age,
            gender=gender,
            map_value=map_value,
        )

    def predict(self, features: dict | None = None) -> dict:
        # Direct arbitrary feature dictionaries are intentionally unsupported:
        # they can bypass the shared online feature-engineering contract.
        raise ValueError("Call predict_patient() with raw vitals and a patient_key.")

    def predict_patient(
        self,
        heart_rate: float | None,
        temperature: float | None,
        sbp: float | None,
        dbp: float | None,
        respiratory_rate: float | None,
        age: float | None = None,
        gender: str | int | float | None = None,
        map_value: float | None = None,
        patient_key: str | None = None,
        **_ignored: Any,
    ) -> dict:
        return self.add_vital_signs(
            heart_rate=heart_rate,
            temperature=temperature,
            sbp=sbp,
            dbp=dbp,
            respiratory_rate=respiratory_rate,
            age=age,
            gender=gender,
            map_value=map_value,
            patient_key=patient_key,
        )

    def get_risk_level(self, probability: float) -> str:
        return self.predictor.get_risk_level(probability)

    def reset_history(self, patient_key: str | None = None) -> None:
        self.predictor.reset_history(patient_key or self.default_patient_key)


def load_predictor(models_dir: str = "models") -> SepsisPredictor:
    # models_dir remains accepted for backwards compatibility; runtime artifacts
    # are intentionally loaded only from the canonical backend/models directory.
    return SepsisPredictor()


if __name__ == "__main__":
    predictor = load_predictor()
    if not predictor.predictor.is_ready:
        raise SystemExit(f"Model not ready: {predictor.predictor.load_error}")
    result = predictor.predict_patient(
        patient_key="demo-patient-1",
        age=50,
        gender="M",
        heart_rate=108,
        temperature=38.1,
        sbp=100,
        dbp=65,
        respiratory_rate=24,
    )
    print("Prediction:", result)

"""Runtime predictor using the same feature schema as offline training.

This module deliberately refuses to use the legacy 114-feature artifact.
Retrain with scripts/run_training.py before enabling inference.
"""
from __future__ import annotations

import json
import threading
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BACKEND_DIR / "models"
MODEL_PATH = MODEL_DIR / "deterioration_model.pkl"
PREPROCESSOR_PATH = MODEL_DIR / "preprocessing_pipeline.pkl"
FEATURE_COLUMNS_PATH = MODEL_DIR / "feature_columns.json"
RISK_THRESHOLDS_PATH = MODEL_DIR / "risk_thresholds.json"
METADATA_PATH = MODEL_DIR / "model_metadata.json"
HISTORY_LIMIT = 20


class ModelNotReadyError(RuntimeError):
    """Raised when checked-in model artifacts don't match the runtime schema."""


class SepsisPredictor:
    """Model loader with patient-scoped short histories for real-time trend features."""

    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.feature_columns: list[str] = []
        self.risk_thresholds: dict[str, Any] = {}
        self.metadata: dict[str, Any] = {}
        self.history_by_patient = defaultdict(lambda: deque(maxlen=HISTORY_LIMIT))
        self._lock = threading.RLock()
        self.load_error: str | None = None
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        try:
            from scripts.feature_engineering import FEATURE_SCHEMA_VERSION, get_feature_columns
            required = [MODEL_PATH, PREPROCESSOR_PATH, FEATURE_COLUMNS_PATH, RISK_THRESHOLDS_PATH, METADATA_PATH]
            missing = [str(p) for p in required if not p.exists()]
            if missing:
                raise ModelNotReadyError(f"Missing trained model artifacts: {', '.join(missing)}")

            metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
            columns = json.loads(FEATURE_COLUMNS_PATH.read_text(encoding="utf-8"))
            if metadata.get("model_schema_version") != FEATURE_SCHEMA_VERSION:
                raise ModelNotReadyError(
                    "The saved model uses an incompatible feature schema. "
                    "Run 'uv run python scripts/run_training.py --data-dir data' from backend."
                )
            expected = get_feature_columns()
            if columns != expected or metadata.get("feature_columns") != expected:
                raise ModelNotReadyError("Saved feature columns do not match runtime schema; retraining is required.")

            model = joblib.load(MODEL_PATH)
            preprocessor = joblib.load(PREPROCESSOR_PATH)
            if not hasattr(model, "predict_proba"):
                raise ModelNotReadyError("Saved classifier does not provide probabilities.")
            if getattr(preprocessor, "n_features_in_", len(columns)) != len(columns):
                raise ModelNotReadyError("Preprocessor feature count does not match saved feature schema.")

            thresholds = json.loads(RISK_THRESHOLDS_PATH.read_text(encoding="utf-8"))
            self.model = model
            self.preprocessor = preprocessor
            self.feature_columns = columns
            self.risk_thresholds = thresholds
            self.metadata = metadata
            self.load_error = None
        except Exception as exc:
            self.model = None
            self.preprocessor = None
            self.load_error = str(exc)

    @property
    def is_ready(self) -> bool:
        return self.model is not None and self.preprocessor is not None and not self.load_error

    def health(self) -> dict:
        return {
            "model_loaded": self.is_ready,
            "schema_version": self.metadata.get("model_schema_version"),
            "selected_model": self.metadata.get("selected_model"),
            "feature_count": len(self.feature_columns),
            "error": self.load_error,
            "clinical_validation": bool(self.metadata.get("clinical_validation", False)),
        }

    @staticmethod
    def _valid_number(value):
        if value is None:
            return np.nan
        try:
            number = float(value)
        except (TypeError, ValueError):
            return np.nan
        return number if np.isfinite(number) else np.nan

    def add_vital_signs(
        self,
        patient_key: str,
        heart_rate: float | None,
        temperature: float | None,
        sbp: float | None,
        dbp: float | None,
        respiratory_rate: float | None,
        age: float | None = None,
        gender: str | int | float | None = None,
        map_value: float | None = None,
    ) -> dict:
        from scripts.feature_engineering import engineer_patient_features, get_feature_columns

        if not patient_key or not str(patient_key).strip():
            raise ValueError("patient_id is required to isolate live histories per patient.")
        if not self.is_ready:
            raise ModelNotReadyError(self.load_error or "Model artifacts are not ready.")

        record = {
            "Age": self._valid_number(age),
            "Gender": gender,
            "HR": self._valid_number(heart_rate),
            "Temp": self._valid_number(temperature),
            "SBP": self._valid_number(sbp),
            "DBP": self._valid_number(dbp),
            "Resp": self._valid_number(respiratory_rate),
            "MAP": self._valid_number(map_value),
            "ICULOS": None,
        }
        with self._lock:
            history = self.history_by_patient[str(patient_key)]
            record["ICULOS"] = (history[-1]["ICULOS"] + 1) if history else 1
            history.append(record.copy())
            frame = engineer_patient_features(pd.DataFrame(list(history)))
            latest = frame.iloc[[-1]][get_feature_columns()]
            x = latest[self.feature_columns].to_numpy(dtype=float)
            transformed = self.preprocessor.transform(x)
            probability = float(self.model.predict_proba(transformed)[0, 1])
            level = self.get_risk_level(probability)
            threshold = float(self.metadata.get("classification_threshold", 0.5))
            return {
                "risk_probability": probability,
                "risk_level": level,
                "prediction": int(probability >= threshold),
                "classification_threshold": threshold,
                "model_name": self.metadata.get("selected_model"),
                "feature_schema_version": self.metadata.get("model_schema_version"),
                "history_points": len(history),
                "clinical_decision_support_only": True,
                "clinical_validation": False,
            }

    def get_risk_level(self, probability: float) -> str:
        for level in ("CRITICAL", "HIGH", "MODERATE", "LOW"):
            bounds = self.risk_thresholds.get(level)
            if not isinstance(bounds, list) or len(bounds) != 2:
                continue
            low, high = bounds
            if level == "CRITICAL" and probability >= low:
                return level
            if low <= probability < high:
                return level
        return "LOW"

    def reset_history(self, patient_key: str | None = None) -> None:
        with self._lock:
            if patient_key is None:
                self.history_by_patient.clear()
            else:
                self.history_by_patient.pop(str(patient_key), None)


_predictor_instance: SepsisPredictor | None = None
_predictor_lock = threading.Lock()


def load_predictor() -> SepsisPredictor:
    global _predictor_instance
    with _predictor_lock:
        if _predictor_instance is None:
            _predictor_instance = SepsisPredictor()
        return _predictor_instance


def reset_predictor(patient_key: str | None = None) -> None:
    """Clear one patient's history, or all in-memory histories when no key is given."""
    load_predictor().reset_history(patient_key)


def predict_patient_standalone(**kwargs) -> dict:
    """Compatibility wrapper that uses shared state, not a fresh history per call."""
    patient_key = kwargs.pop("patient_key", None) or kwargs.pop("patient_id", None)
    return load_predictor().add_vital_signs(patient_key=patient_key, **kwargs)

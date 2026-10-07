import numpy as np
import pandas as pd
import joblib
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")


class SepsisPredictor:
    """
    Real-time sepsis risk predictor maintaining patient history.
    """

    def __init__(
        self,
        model_path: str,
        preprocessor_path: str,
        feature_columns_path: str,
        risk_thresholds_path: str,
        vital_columns: List[str] = None
    ):
        self.model = joblib.load(model_path)
        self.preprocessor = joblib.load(preprocessor_path)

        with open(feature_columns_path, "r") as f:
            self.feature_columns = json.load(f)

        with open(risk_thresholds_path, "r") as f:
            self.risk_thresholds = json.load(f)

        self.vital_columns = vital_columns or ["HR", "O2Sat", "Temp", "SBP", "MAP", "DBP", "Resp"]
        self.history_buffer = []
        self.max_history = 20

    def add_vital_signs(
        self,
        heart_rate: float,
        spo2: float,
        temperature: float,
        sbp: float,
        dbp: float,
        respiratory_rate: float,
        map_value: Optional[float] = None,
        icu_los: Optional[float] = None
    ) -> Dict:
        """
        Add new vital signs to patient history and compute features.
        """
        if map_value is None:
            map_value = (sbp + 2 * dbp) / 3

        record = {
            "HR": heart_rate,
            "O2Sat": spo2,
            "Temp": temperature,
            "SBP": sbp,
            "DBP": dbp,
            "MAP": map_value,
            "Resp": respiratory_rate,
        }
        if icu_los is not None:
            record["ICULOS"] = icu_los

        self.history_buffer.append(record)
        if len(self.history_buffer) > self.max_history:
            self.history_buffer.pop(0)

        return self._compute_features()

    def _compute_features(self) -> Dict:
        """Compute temporal features from history buffer."""
        if len(self.history_buffer) == 0:
            return {}

        df = pd.DataFrame(self.history_buffer)
        df["ICULOS"] = range(1, len(df) + 1) if "ICULOS" not in df.columns else df["ICULOS"]

        from feature_engineering import engineer_patient_features, get_feature_columns
        df_feat = engineer_patient_features(df)

        latest = df_feat.iloc[[-1]]

        feat_cols = get_feature_columns(df_feat)
        missing_cols = set(self.feature_columns) - set(feat_cols)
        for col in missing_cols:
            latest[col] = np.nan

        latest = latest[self.feature_columns]

        return latest.iloc[0].to_dict()

    def predict(self, features: Dict) -> Dict:
        """
        Run prediction on computed features.
        """
        X = pd.DataFrame([features])[self.feature_columns].values
        X_transformed = self.preprocessor.transform(X)

        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X_transformed)[0, 1]
        else:
            proba = float(self.model.predict(X_transformed)[0])

        prediction = int(proba >= 0.5)
        risk_level = self.get_risk_level(proba)

        return {
            "risk_probability": float(proba),
            "risk_level": risk_level,
            "prediction": prediction,
            "thresholds": self.risk_thresholds
        }

    def get_risk_level(self, probability: float) -> str:
        """Convert probability to risk level."""
        for level in ["CRITICAL", "HIGH", "MODERATE", "LOW"]:
            low, high = self.risk_thresholds[level]
            if low <= probability < high:
                return level
        return "LOW"

    def predict_patient(
        self,
        heart_rate: float,
        spo2: float,
        temperature: float,
        sbp: float,
        dbp: float,
        respiratory_rate: float,
        map_value: Optional[float] = None,
        icu_los: Optional[float] = None
    ) -> Dict:
        """
        Main prediction function - add vitals and predict.
        """
        features = self.add_vital_signs(
            heart_rate, spo2, temperature, sbp, dbp, respiratory_rate,
            map_value, icu_los
        )
        if not features:
            return {"error": "No features computed"}

        return self.predict(features)

    def reset_history(self):
        """Clear patient history for new patient."""
        self.history_buffer = []


def load_predictor(
    models_dir: str = "models"
) -> SepsisPredictor:
    """Factory function to load predictor from saved artifacts."""
    return SepsisPredictor(
        model_path=f"{models_dir}/deterioration_model.pkl",
        preprocessor_path=f"{models_dir}/preprocessing_pipeline.pkl",
        feature_columns_path=f"{models_dir}/feature_columns.json",
        risk_thresholds_path=f"{models_dir}/risk_thresholds.json"
    )


if __name__ == "__main__":
    predictor = SepsisPredictor(
        model_path="models/deterioration_model.pkl",
        preprocessor_path="models/preprocessing_pipeline.pkl",
        feature_columns_path="models/feature_columns.json",
        risk_thresholds_path="models/risk_thresholds.json"
    )

    result = predictor.predict_patient(
        heart_rate=108,
        spo2=92,
        temperature=38.1,
        sbp=100,
        dbp=65,
        respiratory_rate=24
    )
    print("Prediction:", result)
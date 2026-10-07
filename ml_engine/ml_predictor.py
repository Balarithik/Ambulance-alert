import json
import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List


# Model artifact paths
# Models are at ./models/ relative to the backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent  # -> /E/projects/Ambulance Alert Sys/backend
MODEL_DIR = BACKEND_DIR / "models"
MODEL_PATH = MODEL_DIR / "deterioration_model.pkl"
PREPROCESSOR_PATH = MODEL_DIR / "preprocessing_pipeline.pkl"
FEATURE_COLUMNS_PATH = MODEL_DIR / "feature_columns.json"
RISK_THRESHOLDS_PATH = MODEL_DIR / "risk_thresholds.json"


class SepsisPredictor:
    """Wrapper for the sepsis/deterioration risk model."""
    
    def __init__(self):
        self.model = self._load_model(MODEL_PATH)
        self.preprocessor = self._load_model(PREPROCESSOR_PATH)
        
        with open(FEATURE_COLUMNS_PATH, "r") as f:
            self.feature_columns = json.load(f)
        
        with open(RISK_THRESHOLDS_PATH, "r") as f:
            self.risk_thresholds = json.load(f)
        
        self.history_buffer = []
        self.max_history = 20
    
    def _load_model(self, path: Path):
        """Load a model artifact."""
        if path.exists():
            return joblib.load(path)
        return None
    
    def add_vital_signs(
        self,
        heart_rate: float,
        temperature: float,
        sbp: float,
        dbp: float,
        respiratory_rate: float,
    ) -> Dict:
        """Add vital signs to history and compute features."""
        map_value = (sbp + 2 * dbp) / 3
        
        record = {
            "HR": heart_rate,
            "Temp": temperature,
            "SBP": sbp,
            "DBP": dbp,
            "Resp": respiratory_rate,
            "MAP": map_value,
        }
        
        self.history_buffer.append(record)
        if len(self.history_buffer) > self.max_history:
            self.history_buffer.pop(0)
        
        return self._compute_features()
    
    def _compute_features(self) -> Dict:
        """Compute temporal features from history buffer."""
        if len(self.history_buffer) == 0:
            return {}
        
        df = pd.DataFrame(self.history_buffer)
        if "ICULOS" not in df.columns:
            df["ICULOS"] = range(1, len(df) + 1)
        
        # Add scripts directory to sys.path if needed
        import sys
        scripts_dir = str(BACKEND_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        from feature_engineering import engineer_patient_features, get_feature_columns
        df_feat = engineer_patient_features(df)
        
        latest = df_feat.iloc[[-1]]
        
        # Ensure all required feature columns exist
        feat_cols = get_feature_columns(df_feat)
        missing_cols = set(self.feature_columns) - set(feat_cols)
        for col in missing_cols:
            latest[col] = np.nan
        
        # Select only the features the model expects
        latest = latest[self.feature_columns]
        
        return latest.iloc[0].to_dict()
    
    def get_risk_level(self, probability: float) -> str:
        """Convert probability to risk level using risk_thresholds."""
        if not self.risk_thresholds:
            if probability >= 0.75:
                return "CRITICAL"
            elif probability >= 0.50:
                return "HIGH"
            elif probability >= 0.25:
                return "MODERATE"
            return "LOW"
            
        for level in ["CRITICAL", "HIGH", "MODERATE", "LOW"]:
            if level in self.risk_thresholds:
                low, high = self.risk_thresholds[level]
                if low <= probability <= high or (level == "CRITICAL" and probability >= low):
                    return level
        return "LOW"

    def predict(self, features: Dict) -> Dict:
        """Run prediction on computed features."""
        if self.model is None or self.preprocessor is None:
            return {
                "risk_probability": 0.0,
                "risk_level": "LOW",
                "error": "Model not loaded",
            }
        
        try:
            # Ensure feature_columns is loaded
            if not self.feature_columns:
                with open(FEATURE_COLUMNS_PATH, "r") as f:
                    self.feature_columns = json.load(f)
            
            X = pd.DataFrame([features])[self.feature_columns].values
            X_transformed = self.preprocessor.transform(X)
            
            if hasattr(self.model, "predict_proba"):
                proba = float(self.model.predict_proba(X_transformed)[0, 1])
            else:
                proba = float(self.model.predict(X_transformed)[0])
            
            prediction = int(proba >= 0.5)
            risk_level = self.get_risk_level(proba)
            
            return {
                "risk_probability": proba,
                "risk_level": risk_level,
                "prediction": prediction,
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "risk_probability": 0.0,
                "risk_level": "LOW",
                "error": str(e),
            }
    
    def predict_patient(
        self,
        heart_rate: float,
        temperature: float,
        sbp: float,
        dbp: float,
        respiratory_rate: float,
    ) -> Dict:
        """Main prediction function."""
        features = self.add_vital_signs(
            heart_rate=heart_rate,
            temperature=temperature,
            sbp=sbp,
            dbp=dbp,
            respiratory_rate=respiratory_rate,
        )
        
        if "error" in features:
            return features
        
        return self.predict(features)


# Module-level standalone function for API use
def predict_patient_standalone(
    heart_rate: float,
    temperature: float,
    sbp: float,
    dbp: float,
    respiratory_rate: float,
) -> Dict:
    """Standalone prediction function - creates predictor and runs inference."""
    predictor = SepsisPredictor()
    return predictor.predict_patient(
        heart_rate=heart_rate,
        temperature=temperature,
        sbp=sbp,
        dbp=dbp,
        respiratory_rate=respiratory_rate,
    )


# Factory function
_predictor_instance = None


def load_predictor() -> SepsisPredictor:
    """Factory function to load predictor from saved artifacts."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = SepsisPredictor()
    return _predictor_instance


def reset_predictor():
    """Reset the predictor instance (useful for testing)."""
    global _predictor_instance
    _predictor_instance = None

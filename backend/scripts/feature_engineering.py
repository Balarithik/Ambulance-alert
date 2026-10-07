import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings("ignore")


VITAL_COLUMNS = ["HR", "O2Sat", "Temp", "SBP", "MAP", "DBP", "Resp"]
ROLLING_WINDOW = 6


def create_temporal_features(df: pd.DataFrame, vital_cols: List[str], window: int = ROLLING_WINDOW) -> pd.DataFrame:
    """
    Create temporal features for vital signs using only past information.
    Features: current, previous, change, rolling mean/min/max/std, trend.
    """
    df = df.copy()
    df = df.sort_values("ICULOS").reset_index(drop=True)

    for col in vital_cols:
        if col not in df.columns:
            continue

        values = df[col].values

        df[f"{col}_prev"] = df[col].shift(1)
        df[f"{col}_change"] = df[col] - df[f"{col}_prev"]

        df[f"{col}_rolling_mean"] = df[col].rolling(window=window, min_periods=1).mean()
        df[f"{col}_rolling_min"] = df[col].rolling(window=window, min_periods=1).min()
        df[f"{col}_rolling_max"] = df[col].rolling(window=window, min_periods=1).max()
        df[f"{col}_rolling_std"] = df[col].rolling(window=window, min_periods=1).std()

        df[f"{col}_trend"] = df[col].rolling(window=window, min_periods=2).apply(
            lambda x: np.polyfit(np.arange(len(x)), x, 1)[0] if len(x) >= 2 else 0,
            raw=True
        )

    return df


def add_static_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add static patient features."""
    df = df.copy()

    if "Age" in df.columns:
        df["age"] = df["Age"].iloc[0] if df["Age"].notna().any() else np.nan

    if "Gender" in df.columns:
        df["gender"] = df["Gender"].iloc[0] if df["Gender"].notna().any() else np.nan

    if "HospAdmTime" in df.columns:
        df["hosp_adm_time"] = df["HospAdmTime"].iloc[0] if df["HospAdmTime"].notna().any() else np.nan

    return df


def add_aggregate_features(df: pd.DataFrame, vital_cols: List[str]) -> pd.DataFrame:
    """Add aggregate statistics per patient (up to current time)."""
    df = df.copy()

    for col in vital_cols:
        if col not in df.columns:
            continue

        expanding = df[col].expanding(min_periods=1)
        df[f"{col}_expanding_mean"] = expanding.mean()
        df[f"{col}_expanding_min"] = expanding.min()
        df[f"{col}_expanding_max"] = expanding.max()
        df[f"{col}_expanding_std"] = expanding.std()

    return df


def engineer_patient_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Complete feature engineering pipeline for a single patient.
    Preserves temporal order and prevents leakage.
    """
    vital_cols = [c for c in VITAL_COLUMNS if c in df.columns]

    df = create_temporal_features(df, vital_cols)
    df = add_static_features(df)
    df = add_aggregate_features(df, vital_cols)

    return df


def get_feature_columns(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> List[str]:
    """Get list of feature columns excluding targets and identifiers."""
    if exclude_cols is None:
        exclude_cols = [
            "patient_id", "dataset_source", "ICULOS", "SepsisLabel",
            "Age", "Gender", "Unit1", "Unit2", "HospAdmTime"
        ]

    feature_cols = [c for c in df.columns if c not in exclude_cols]
    return feature_cols


if __name__ == "__main__":
    from data_loader import load_patient_file
    df = load_patient_file("data/training_setA/p000001.psv", "A")
    print("Original columns:", df.columns.tolist())
    print("Shape:", df.shape)

    df_feat = engineer_patient_features(df)
    print("\nFeature columns:", get_feature_columns(df_feat))
    print("Shape after feature engineering:", df_feat.shape)
    print("\nSample features:")
    print(df_feat[["HR", "HR_prev", "HR_change", "HR_rolling_mean", "HR_trend", "SepsisLabel"]].head(10))
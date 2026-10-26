"""Shared feature contract for training and ambulance-time inference.

The model uses only the core variables that can be entered/collected by LifeSyncAI.
PhysioNet's additional laboratory/O2Sat columns are intentionally excluded because the
current ambulance hardware does not provide them.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

FEATURE_SCHEMA_VERSION = "ambulance-v2"
ROLLING_WINDOW = 6
BASE_VITAL_COLUMNS = ["HR", "Temp", "SBP", "DBP", "Resp", "MAP"]
TEMPORAL_SUFFIXES = ["prev", "change", "rolling_mean", "rolling_std", "trend"]
STATIC_FEATURE_COLUMNS = ["age", "gender"]
MODEL_FEATURE_COLUMNS = (
    STATIC_FEATURE_COLUMNS
    + BASE_VITAL_COLUMNS
    + [f"{vital}_{suffix}" for vital in BASE_VITAL_COLUMNS for suffix in TEMPORAL_SUFFIXES]
)


def normalize_gender(value):
    """Map PhysioNet's 0=female / 1=male encoding and common UI strings consistently."""
    if value is None or pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        number = float(value)
        return number if number in (0.0, 1.0) else np.nan

    label = str(value).strip().lower()
    if label in {"0", "0.0", "f", "female", "woman"}:
        return 0.0
    if label in {"1", "1.0", "m", "male", "man"}:
        return 1.0
    return np.nan


def _trend_slope(values: np.ndarray) -> float:
    """Least-squares slope for a short, time-ordered window; ignore missing points."""
    values = np.asarray(values, dtype=float)
    valid = np.isfinite(values)
    if valid.sum() < 2:
        return 0.0 if valid.sum() == 1 else np.nan
    x = np.arange(len(values), dtype=float)[valid]
    y = values[valid]
    return float(np.polyfit(x, y, 1)[0])


def _to_numeric_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    for column in columns:
        if column not in df.columns:
            df[column] = np.nan
        df[column] = pd.to_numeric(df[column], errors="coerce")
        df[column] = df[column].replace([np.inf, -np.inf], np.nan)
    return df


def engineer_patient_features(df: pd.DataFrame, window: int = ROLLING_WINDOW) -> pd.DataFrame:
    """Create online-safe features from one patient's time-ordered vital history.

    This function is shared by offline training and runtime prediction. It only uses
    the current and previous rows; no future measurements are referenced.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["ICULOS", *MODEL_FEATURE_COLUMNS, "SepsisLabel"])

    if window < 2:
        raise ValueError("window must be at least 2")

    frame = df.copy()
    if "ICULOS" not in frame.columns:
        frame["ICULOS"] = np.arange(1, len(frame) + 1)
    frame = frame.sort_values("ICULOS", kind="stable").reset_index(drop=True)

    # Accept the canonical dataset names as well as values already prepared by an API.
    if "Age" not in frame.columns and "age" in frame.columns:
        frame["Age"] = frame["age"]
    if "Gender" not in frame.columns and "gender" in frame.columns:
        frame["Gender"] = frame["gender"]

    if "Age" in frame.columns:
        frame["age"] = pd.to_numeric(frame["Age"], errors="coerce")
    else:
        frame["age"] = np.nan

    if "Gender" in frame.columns:
        frame["gender"] = frame["Gender"].map(normalize_gender)
    else:
        frame["gender"] = np.nan

    # Normalize core vitals. MAP is derived from BP when both pressures are present.
    _to_numeric_columns(frame, ["HR", "Temp", "SBP", "DBP", "Resp"])
    source_map = pd.to_numeric(frame["MAP"], errors="coerce") if "MAP" in frame.columns else pd.Series(np.nan, index=frame.index)
    source_map = source_map.replace([np.inf, -np.inf], np.nan)
    derived_map = (frame["SBP"] + 2.0 * frame["DBP"]) / 3.0
    frame["MAP"] = derived_map.where(derived_map.notna(), source_map)

    for vital in BASE_VITAL_COLUMNS:
        current = frame[vital]
        rolling = current.rolling(window=window, min_periods=1)
        frame[f"{vital}_prev"] = current.shift(1)
        frame[f"{vital}_change"] = current - frame[f"{vital}_prev"]
        frame[f"{vital}_rolling_mean"] = rolling.mean()
        frame[f"{vital}_rolling_std"] = rolling.std(ddof=0)
        frame[f"{vital}_trend"] = current.rolling(
            window=window, min_periods=1
        ).apply(_trend_slope, raw=True)

    # Keep one deterministic feature schema in both training and inference.
    for column in MODEL_FEATURE_COLUMNS:
        if column not in frame.columns:
            frame[column] = np.nan
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame[column] = frame[column].replace([np.inf, -np.inf], np.nan)

    return frame


def get_feature_columns(_df: pd.DataFrame | None = None) -> list[str]:
    """Return the fixed, deployment-compatible feature order."""
    return list(MODEL_FEATURE_COLUMNS)


def create_temporal_features(
    df: pd.DataFrame, vital_cols: list[str] | None = None, window: int = ROLLING_WINDOW
) -> pd.DataFrame:
    """Compatibility wrapper for older training scripts."""
    return engineer_patient_features(df, window=window)


def add_static_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compatibility wrapper; full engineering produces the normalized static fields."""
    result = df.copy()
    if "Age" in result.columns:
        result["age"] = pd.to_numeric(result["Age"], errors="coerce")
    if "Gender" in result.columns:
        result["gender"] = result["Gender"].map(normalize_gender)
    return result


def add_aggregate_features(df: pd.DataFrame, vital_cols: list[str] | None = None) -> pd.DataFrame:
    """Deprecated compatibility wrapper.

    Expanding statistics were removed because training them over full patient histories
    did not match the truncated, live ambulance history.
    """
    return df.copy()


if __name__ == "__main__":
    sample = pd.DataFrame(
        [
            {"ICULOS": 1, "Age": 50, "Gender": 1, "HR": 85, "Temp": 37.0, "SBP": 120, "DBP": 80, "Resp": 16},
            {"ICULOS": 2, "Age": 50, "Gender": 1, "HR": 96, "Temp": 37.4, "SBP": 118, "DBP": 78, "Resp": 18},
        ]
    )
    engineered = engineer_patient_features(sample)
    print("Schema version:", FEATURE_SCHEMA_VERSION)
    print("Feature count:", len(get_feature_columns(engineered)))
    print(engineered[get_feature_columns(engineered)].tail(1).to_string(index=False))

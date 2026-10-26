"""Preprocessing utilities for the LifeSyncAI ambulance-compatible model."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler


def create_preprocessing_pipeline(
    feature_columns: Sequence[str] | None = None,
    numeric_features: Sequence[str] | None = None,
    scaler_type: str = "robust",
) -> Pipeline:
    """Build an imputer/scaler pipeline. Fit it on training rows only."""
    if scaler_type == "robust":
        scaler = RobustScaler()
    elif scaler_type == "standard":
        scaler = StandardScaler()
    elif scaler_type == "none":
        scaler = "passthrough"
    else:
        raise ValueError("scaler_type must be robust, standard, or none")

    return Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scaler", scaler),
    ])


def prepare_data_for_training(
    df: pd.DataFrame,
    feature_columns: Sequence[str],
    target_column: str = "SepsisLabel",
) -> tuple[np.ndarray, np.ndarray]:
    missing = [c for c in feature_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Training frame missing required features: {missing}")
    if target_column not in df.columns:
        raise ValueError(f"Training frame missing target column: {target_column}")
    X = df[list(feature_columns)].apply(pd.to_numeric, errors="coerce").replace(
        [np.inf, -np.inf], np.nan
    ).to_numpy(dtype=float)
    y = pd.to_numeric(df[target_column], errors="coerce").to_numpy()
    valid = np.isfinite(y) & np.isin(y, [0, 1])
    return X[valid], y[valid].astype(int)


def split_patients_by_id(
    patient_ids: Sequence[str],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42,
) -> tuple[list[str], list[str], list[str]]:
    if not np.isclose(train_ratio + val_ratio + test_ratio, 1.0):
        raise ValueError("Train/validation/test ratios must sum to 1.")
    ids = np.asarray(list(patient_ids), dtype=object)
    if len(ids) < 3:
        raise ValueError("At least 3 unique patients are required for patient-level splitting.")
    shuffled = np.random.default_rng(random_state).permutation(ids)
    n_train = max(1, int(len(shuffled) * train_ratio))
    n_val = max(1, int(len(shuffled) * val_ratio))
    if n_train + n_val >= len(shuffled):
        n_train, n_val = len(shuffled) - 2, 1
    train_ids = shuffled[:n_train].tolist()
    val_ids = shuffled[n_train:n_train + n_val].tolist()
    test_ids = shuffled[n_train + n_val:].tolist()
    assert not (set(train_ids) & set(val_ids) or set(train_ids) & set(test_ids) or set(val_ids) & set(test_ids))
    return train_ids, val_ids, test_ids


def fit_preprocessor(train_dfs: list[pd.DataFrame], feature_columns: Sequence[str]) -> Pipeline:
    arrays = [prepare_data_for_training(df, feature_columns)[0] for df in train_dfs]
    arrays = [array for array in arrays if len(array)]
    if not arrays:
        raise ValueError("No usable training rows were provided.")
    pipeline = create_preprocessing_pipeline(feature_columns, feature_columns)
    pipeline.fit(np.vstack(arrays))
    return pipeline


def apply_preprocessor(
    dfs: list[pd.DataFrame], feature_columns: Sequence[str], preprocessor: Pipeline
) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = [], []
    for df in dfs:
        x, y = prepare_data_for_training(df, feature_columns)
        if len(x):
            xs.append(x)
            ys.append(y)
    if not xs:
        raise ValueError("No usable rows were found for this split.")
    x = np.vstack(xs)
    y = np.concatenate(ys)
    return preprocessor.transform(x), y


def save_preprocessor(preprocessor: Pipeline, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, path)


def load_preprocessor(path: str | Path) -> Pipeline:
    return joblib.load(path)


def save_feature_columns(feature_columns: Sequence[str], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(list(feature_columns), indent=2), encoding="utf-8")


def load_feature_columns(path: str | Path) -> list[str]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

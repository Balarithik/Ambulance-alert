import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from typing import List, Tuple, Optional
import joblib
import json


def create_preprocessing_pipeline(
    feature_columns: List[str],
    numeric_features: List[str],
    scaler_type: str = "robust"
) -> Pipeline:
    """
    Create a preprocessing pipeline for the features.
    Uses RobustScaler for medical data (handles outliers better).
    """
    if scaler_type == "robust":
        scaler = RobustScaler()
    else:
        scaler = StandardScaler()

    preprocessor = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", scaler)
    ])

    return preprocessor


def prepare_data_for_training(
    df: pd.DataFrame,
    feature_columns: List[str],
    target_column: str = "SepsisLabel"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare features and target arrays from patient DataFrame.
    """
    X = df[feature_columns].values
    y = df[target_column].values.astype(int)
    return X, y


def split_patients_by_id(
    patient_ids: List[str],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42
) -> Tuple[List[str], List[str], List[str]]:
    """
    Split patient IDs into train/val/test with no overlap.
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "Ratios must sum to 1"

    np.random.seed(random_state)
    shuffled = np.random.permutation(patient_ids)

    n_train = int(len(shuffled) * train_ratio)
    n_val = int(len(shuffled) * val_ratio)

    train_ids = shuffled[:n_train].tolist()
    val_ids = shuffled[n_train:n_train + n_val].tolist()
    test_ids = shuffled[n_train + n_val:].tolist()

    assert len(set(train_ids) & set(val_ids)) == 0
    assert len(set(train_ids) & set(test_ids)) == 0
    assert len(set(val_ids) & set(test_ids)) == 0

    return train_ids, val_ids, test_ids


def fit_preprocessor(
    train_dfs: List[pd.DataFrame],
    feature_columns: List[str]
) -> Pipeline:
    """Fit preprocessor on training data only."""
    X_train_list = []
    for df in train_dfs:
        X, _ = prepare_data_for_training(df, feature_columns)
        X_train_list.append(X)
    X_train = np.vstack(X_train_list) if X_train_list else np.array([])

    preprocessor = create_preprocessing_pipeline(feature_columns, feature_columns)
    preprocessor.fit(X_train)
    return preprocessor


def apply_preprocessor(
    dfs: List[pd.DataFrame],
    feature_columns: List[str],
    preprocessor: Pipeline
) -> Tuple[np.ndarray, np.ndarray]:
    """Apply fitted preprocessor to list of DataFrames."""
    X_list, y_list = [], []
    for df in dfs:
        X, y = prepare_data_for_training(df, feature_columns)
        X_list.append(X)
        y_list.append(y)

    if not X_list:
        return np.array([]), np.array([])

    X = np.vstack(X_list)
    y = np.hstack(y_list)

    X_transformed = preprocessor.transform(X)
    return X_transformed, y


def save_preprocessor(preprocessor: Pipeline, path: str):
    """Save preprocessing pipeline."""
    joblib.dump(preprocessor, path)


def load_preprocessor(path: str) -> Pipeline:
    """Load preprocessing pipeline."""
    return joblib.load(path)


def save_feature_columns(feature_columns: List[str], path: str):
    """Save feature column names."""
    with open(path, "w") as f:
        json.dump(feature_columns, f)


def load_feature_columns(path: str) -> List[str]:
    """Load feature column names."""
    with open(path, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    from data_loader import load_patient_file
    from feature_engineering import engineer_patient_features, get_feature_columns

    df = load_patient_file("data/training_setA/p000001.psv", "A")
    df_feat = engineer_patient_features(df)
    feat_cols = get_feature_columns(df_feat)

    print("Feature columns:", feat_cols)
    print("Count:", len(feat_cols))

    preprocessor = create_preprocessing_pipeline(feat_cols, feat_cols)
    X, y = prepare_data_for_training(df_feat, feat_cols)
    print("X shape:", X.shape)
    print("y shape:", y.shape)

    preprocessor.fit(X)
    X_trans = preprocessor.transform(X)
    print("Transformed X shape:", X_trans.shape)
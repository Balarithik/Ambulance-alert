import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    roc_curve, precision_recall_curve
)
import joblib
import json
import warnings
warnings.filterwarnings("ignore")


def get_models(class_weight: str = "balanced"):
    """Get model instances with reasonable defaults for 8GB RAM."""
    models = {
        "LogisticRegression": LogisticRegression(
            class_weight=class_weight,
            max_iter=1000,
            solver="lbfgs",
            n_jobs=-1,
            random_state=42
        ),
        "RandomForest": RandomForestClassifier(
            class_weight=class_weight,
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            n_jobs=-1,
            random_state=42
        ),
        "XGBoost": XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=1,
            n_jobs=-1,
            random_state=42,
            eval_metric="logloss",
            verbosity=0
        )
    }
    return models


def get_param_distributions():
    """Get parameter distributions for randomized search."""
    return {
        "LogisticRegression": {
            "C": np.logspace(-3, 2, 10),
            "penalty": ["l2"],
        },
        "RandomForest": {
            "n_estimators": [100, 200, 300],
            "max_depth": [10, 15, 20, None],
            "min_samples_split": [5, 10, 20],
            "min_samples_leaf": [2, 5, 10],
        },
        "XGBoost": {
            "n_estimators": [100, 200, 300],
            "max_depth": [4, 6, 8],
            "learning_rate": [0.05, 0.1, 0.2],
            "subsample": [0.7, 0.8, 0.9],
            "colsample_bytree": [0.7, 0.8, 0.9],
        }
    }


def train_model_with_search(
    model,
    param_dist: dict,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    n_iter: int = 10,
    cv: int = 3,
    scoring: str = "f1"
):
    """Train model with randomized search on validation set."""
    if model is None:
        return None, {}

    search = RandomizedSearchCV(
        model,
        param_dist,
        n_iter=n_iter,
        cv=cv,
        scoring=scoring,
        n_jobs=-1,
        random_state=42,
        verbose=0
    )

    search.fit(X_train, y_train)

    best_model = search.best_estimator_

    y_pred = best_model.predict(X_val)
    y_proba = best_model.predict_proba(X_val)[:, 1] if hasattr(best_model, "predict_proba") else y_pred

    metrics = compute_metrics(y_val, y_pred, y_proba)

    return best_model, metrics


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> dict:
    """Compute all evaluation metrics."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "specificity": tn / (tn + fp) if (tn + fp) > 0 else 0,
        "roc_auc": roc_auc_score(y_true, y_proba) if len(np.unique(y_true)) > 1 else 0,
        "pr_auc": average_precision_score(y_true, y_proba) if len(np.unique(y_true)) > 1 else 0,
        "confusion_matrix": {
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)
        }
    }


def train_all_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    class_weight: str = "balanced"
) -> dict:
    """Train all three models and return results."""
    models = get_models(class_weight)
    param_dists = get_param_distributions()

    results = {}

    for name, model in models.items():
        print(f"\nTraining {name}...")
        try:
            best_model, metrics = train_model_with_search(
                model,
                param_dists[name],
                X_train, y_train,
                X_val, y_val,
                n_iter=8,
                cv=3,
                scoring="f1"
            )
            results[name] = {
                "model": best_model,
                "metrics": metrics,
                "best_params": search.best_params_ if 'search' in locals() else {}
            }
            print(f"  F1: {metrics['f1']:.4f}, ROC-AUC: {metrics['roc_auc']:.4f}, PR-AUC: {metrics['pr_auc']:.4f}")
        except Exception as e:
            print(f"  ERROR training {name}: {e}")
            results[name] = {"model": None, "metrics": {}, "error": str(e)}

    return results


def select_best_model(results: dict, metric: str = "f1") -> Tuple[str, dict]:
    """Select best model based on validation metric."""
    best_name = None
    best_score = -1

    for name, result in results.items():
        if result.get("model") is not None and metric in result["metrics"]:
            score = result["metrics"][metric]
            if score > best_score:
                best_score = score
                best_name = name

    return best_name, results[best_name] if best_name else (None, {})


def save_model(model, path: str):
    """Save trained model."""
    joblib.dump(model, path)


def load_model(path: str):
    """Load trained model."""
    return joblib.load(path)


def save_metrics(metrics: dict, path: str):
    """Save metrics to JSON."""
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)


if __name__ == "__main__":
    from data_loader import load_patient_file
    from feature_engineering import engineer_patient_features, get_feature_columns
    from preprocessing import create_preprocessing_pipeline, prepare_data_for_training

    df = load_patient_file("data/training_setA/p000001.psv", "A")
    df_feat = engineer_patient_features(df)
    feat_cols = get_feature_columns(df_feat)

    preprocessor = create_preprocessing_pipeline(feat_cols, feat_cols)
    X, y = prepare_data_for_training(df_feat, feat_cols)
    preprocessor.fit(X)
    X_trans = preprocessor.transform(X)

    models = get_models()
    print("Available models:", list(models.keys()))
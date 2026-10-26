"""Train and compare Logistic Regression, Random Forest, and XGBoost."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import RandomizedSearchCV, StratifiedGroupKFold
from xgboost import XGBClassifier


def get_models(class_weight: str | None = "balanced", random_state: int = 42) -> dict:
    """Return the three planned classifiers."""
    return {
        "LogisticRegression": LogisticRegression(
            class_weight=class_weight, max_iter=1500, solver="lbfgs", random_state=random_state
        ),
        "RandomForest": RandomForestClassifier(
            class_weight=class_weight, n_estimators=200, max_depth=15,
            min_samples_split=10, min_samples_leaf=5, n_jobs=-1, random_state=random_state
        ),
        "XGBoost": XGBClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, n_jobs=-1,
            random_state=random_state, eval_metric="logloss", verbosity=0,
            tree_method="hist",
        ),
    }


def get_param_distributions() -> dict:
    return {
        "LogisticRegression": {"C": np.logspace(-3, 2, 8)},
        "RandomForest": {
            "n_estimators": [100, 200, 300], "max_depth": [8, 12, 16, None],
            "min_samples_split": [2, 5, 10], "min_samples_leaf": [1, 2, 5],
        },
        "XGBoost": {
            "n_estimators": [100, 200, 300], "max_depth": [3, 4, 5, 6],
            "learning_rate": [0.03, 0.05, 0.1], "subsample": [0.7, 0.85, 1.0],
            "colsample_bytree": [0.7, 0.85, 1.0],
        },
    }


def compute_metrics(y_true, y_pred, y_proba) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "specificity": float(tn / (tn + fp)) if tn + fp else 0.0,
        "roc_auc": float(roc_auc_score(y_true, y_proba)) if len(np.unique(y_true)) == 2 else None,
        "pr_auc": float(average_precision_score(y_true, y_proba)) if len(np.unique(y_true)) == 2 else None,
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def train_model_with_search(
    model, param_dist: dict, X_train, y_train, X_val, y_val,
    n_iter: int = 8, cv: int = 3, scoring: str = "f1", groups=None,
) -> tuple[object, dict, dict]:
    """Tune using patient-grouped folds; validation is used only for model comparison."""
    if len(np.unique(y_train)) < 2:
        raise ValueError("Training split must contain both target classes.")
    if groups is None:
        raise ValueError("Patient group IDs are required to prevent rows from one patient leaking across CV folds.")
    groups = np.asarray(groups)
    if len(groups) != len(y_train):
        raise ValueError("groups length must match the number of training rows.")
    unique_groups = np.unique(groups)
    folds = min(cv, len(unique_groups))
    if folds < 2:
        raise ValueError("At least two distinct patients are required for grouped cross-validation.")
    cv_splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=42)
    search = RandomizedSearchCV(
        estimator=model, param_distributions=param_dist, n_iter=n_iter,
        cv=cv_splitter,
        scoring=scoring, n_jobs=-1, random_state=42, refit=True, error_score="raise",
    )
    search.fit(X_train, y_train, groups=groups)
    best = search.best_estimator_
    proba = best.predict_proba(X_val)[:, 1]
    # Use a fixed threshold for comparable baseline metrics; tune threshold on validation later.
    metrics = compute_metrics(y_val, (proba >= 0.5).astype(int), proba)
    return best, metrics, dict(search.best_params_)


def train_all_models(X_train, y_train, X_val, y_val, groups_train, class_weight: str = "balanced") -> dict:
    results = {}
    models = get_models(class_weight)
    distributions = get_param_distributions()
    for name, model in models.items():
        print(f"\nTraining {name}...")
        try:
            best, metrics, params = train_model_with_search(
                model, distributions[name], X_train, y_train, X_val, y_val,
                n_iter=6, cv=3, scoring="average_precision", groups=groups_train,
            )
            results[name] = {"model": best, "metrics": metrics, "best_params": params}
            print(f"  Recall={metrics['recall']:.4f} F1={metrics['f1']:.4f} PR-AUC={metrics['pr_auc']}")
        except Exception as exc:
            results[name] = {"model": None, "metrics": {}, "error": str(exc)}
            print(f"  ERROR: {exc}")
    return results


def select_best_model(results: dict, metric: str = "pr_auc") -> tuple[str | None, dict]:
    viable = [
        (name, result) for name, result in results.items()
        if result.get("model") is not None and result.get("metrics", {}).get(metric) is not None
    ]
    if not viable:
        return None, {}
    name, result = max(viable, key=lambda pair: pair[1]["metrics"][metric])
    return name, result


def save_model(model, path: str | Path) -> None:
    import joblib
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_model(path: str | Path):
    import joblib
    return joblib.load(path)


def save_metrics(metrics: dict, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")

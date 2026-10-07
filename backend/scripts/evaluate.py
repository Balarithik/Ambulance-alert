import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix, roc_curve, precision_recall_curve,
    roc_auc_score, average_precision_score
)
import joblib
import json
import warnings
warnings.filterwarnings("ignore")


def evaluate_model(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    threshold: float = 0.5
) -> dict:
    """Evaluate model on test set with given threshold."""
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_test)
    y_pred = (y_proba >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    metrics = {
        "accuracy": (tp + tn) / (tp + tn + fp + fn),
        "precision": tp / (tp + fp) if (tp + fp) > 0 else 0,
        "recall": tp / (tp + fn) if (tp + fn) > 0 else 0,
        "f1": 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0,
        "specificity": tn / (tn + fp) if (tn + fp) > 0 else 0,
        "roc_auc": roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else 0,
        "pr_auc": average_precision_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else 0,
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "y_proba": y_proba,
        "y_pred": y_pred
    }
    return metrics


def plot_confusion_matrix(cm: dict, save_path: str, title: str = "Confusion Matrix"):
    """Plot and save confusion matrix."""
    fig, ax = plt.subplots(figsize=(6, 5))
    cm_array = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
    sns.heatmap(cm_array, annot=True, fmt="d", cmap="Blues", ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def plot_roc_curve(y_true: np.ndarray, y_proba: np.ndarray, save_path: str, model_name: str = "Model"):
    """Plot and save ROC curve."""
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    auc = roc_auc_score(y_true, y_proba)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, label=f"{model_name} (AUC = {auc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", label="Random")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve")
    ax.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def plot_pr_curve(y_true: np.ndarray, y_proba: np.ndarray, save_path: str, model_name: str = "Model"):
    """Plot and save Precision-Recall curve."""
    precision, recall, _ = precision_recall_curve(y_true, y_proba)
    pr_auc = average_precision_score(y_true, y_proba)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(recall, precision, label=f"{model_name} (PR-AUC = {pr_auc:.3f})")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall Curve")
    ax.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def plot_feature_importance(model, feature_names: list, save_path: str, top_n: int = 20):
    """Plot feature importance for tree-based models."""
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1][:top_n]

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.barh(range(len(indices)), importances[indices])
        ax.set_yticks(range(len(indices)))
        ax.set_yticklabels([feature_names[i] for i in indices])
        ax.set_xlabel("Feature Importance")
        ax.set_title(f"Top {top_n} Feature Importances")
        ax.invert_yaxis()
        plt.tight_layout()
        plt.savefig(save_path, dpi=150)
        plt.close()
        return {feature_names[i]: float(importances[i]) for i in indices}
    return {}


def create_comparison_table(results: dict) -> pd.DataFrame:
    """Create comparison table DataFrame."""
    rows = []
    for name, result in results.items():
        if result.get("model") is not None and "metrics" in result:
            m = result["metrics"]
            rows.append({
                "Model": name,
                "Accuracy": m.get("accuracy", 0),
                "Precision": m.get("precision", 0),
                "Recall": m.get("recall", 0),
                "F1": m.get("f1", 0),
                "ROC-AUC": m.get("roc_auc", 0),
                "PR-AUC": m.get("pr_auc", 0)
            })
    return pd.DataFrame(rows)


def save_comparison_table(df: pd.DataFrame, path: str):
    """Save comparison table to CSV."""
    df.to_csv(path, index=False)


def find_optimal_threshold(y_true: np.ndarray, y_proba: np.ndarray, metric: str = "f1") -> float:
    """Find optimal threshold on validation data."""
    from sklearn.metrics import precision_recall_curve
    precision, recall, thresholds = precision_recall_curve(y_true, y_proba)

    if metric == "f1":
        f1_scores = 2 * precision * recall / (precision + recall + 1e-10)
        best_idx = np.argmax(f1_scores[:-1])
        return float(thresholds[best_idx])
    elif metric == "recall":
        valid = recall[:-1] >= 0.8
        if valid.any():
            best_idx = np.argmax(precision[:-1][valid])
            return float(thresholds[:-1][valid][best_idx])
    return 0.5


def define_risk_thresholds(y_true: np.ndarray, y_proba: np.ndarray) -> dict:
    """Define risk level thresholds based on validation data."""
    thresholds = np.percentile(y_proba, [25, 50, 75, 90, 95])

    return {
        "LOW": [0.0, float(thresholds[0])],
        "MODERATE": [float(thresholds[0]), float(thresholds[1])],
        "HIGH": [float(thresholds[1]), float(thresholds[2])],
        "CRITICAL": [float(thresholds[2]), 1.0],
        "percentiles": {
            "p25": float(thresholds[0]),
            "p50": float(thresholds[1]),
            "p75": float(thresholds[2]),
            "p90": float(thresholds[3]),
            "p95": float(thresholds[4])
        }
    }


def get_risk_level(probability: float, thresholds: dict) -> str:
    """Convert probability to risk level."""
    for level in ["CRITICAL", "HIGH", "MODERATE", "LOW"]:
        low, high = thresholds[level]
        if low <= probability < high:
            return level
    return "LOW"


if __name__ == "__main__":
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=1000, n_features=20, random_state=42)
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)

    metrics = evaluate_model(model, X_test, y_test)
    print("Metrics:", {k: v for k, v in metrics.items() if k not in ["y_proba", "y_pred", "confusion_matrix"]})
    print("Confusion Matrix:", metrics["confusion_matrix"])

    thresholds = define_risk_thresholds(y_test, metrics["y_proba"])
    print("Risk thresholds:", thresholds)
#!/usr/bin/env python3
"""Train the LifeSyncAI ambulance-compatible sepsis-risk prototype.

Run from the backend directory:
    uv run python scripts/run_training.py --data-dir data
Expected files: data/training_setA/*.psv and data/training_setB/*.psv
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR / "scripts"))

from data_loader import discover_datasets, load_patient_file
from feature_engineering import (
    FEATURE_SCHEMA_VERSION, engineer_patient_features, get_feature_columns,
)
from preprocessing import (
    split_patients_by_id, fit_preprocessor, apply_preprocessor,
    save_preprocessor, save_feature_columns,
)
from train import train_all_models, select_best_model, save_model, compute_metrics


def choose_f1_threshold(y_true, probabilities) -> float:
    """Choose a threshold on validation data only; never tune on the test set."""
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    if len(thresholds) == 0:
        return 0.5
    f1 = 2 * precision[:-1] * recall[:-1] / (precision[:-1] + recall[:-1] + 1e-12)
    return float(thresholds[int(np.nanargmax(f1))])


def risk_bands_from_validation(probabilities) -> dict:
    """Prototype display bands only; these are not clinical decision thresholds."""
    p25, p50, p75 = [float(x) for x in np.quantile(probabilities, [0.25, 0.50, 0.75])]
    # Ensure nondecreasing boundaries even when many probabilities are tied.
    p50 = max(p50, p25)
    p75 = max(p75, p50)
    return {
        "LOW": [0.0, p25],
        "MODERATE": [p25, p50],
        "HIGH": [p50, p75],
        "CRITICAL": [p75, 1.0],
        "metadata": {
            "schema_version": FEATURE_SCHEMA_VERSION,
            "method": "validation-set probability quartiles",
            "clinical_validation": False,
            "warning": "Prototype display bands only; not clinically validated triage thresholds.",
        },
    }


def process_files(files: list[str], source: str) -> list[pd.DataFrame]:
    patients = []
    for index, path in enumerate(files, start=1):
        frame = load_patient_file(path, source)
        if frame.empty or "SepsisLabel" not in frame.columns:
            continue
        # A file is one patient. IDs are source-prefixed to prevent accidental overlap.
        frame["patient_id"] = f"{source}-{Path(path).stem}"
        engineered = engineer_patient_features(frame)
        if engineered["SepsisLabel"].notna().any():
            patients.append(engineered)
        if index % 1000 == 0:
            print(f"Processed {index}/{len(files)} files from set {source}")
    return patients


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data", help="Directory containing training_setA and training_setB")
    parser.add_argument("--model-dir", default="models", help="Output directory for model artifacts")
    parser.add_argument("--output-dir", default="outputs", help="Output directory for metrics")
    parser.add_argument("--max-patients-per-set", type=int, default=0, help="Optional small smoke-test limit; 0 uses all files")
    args = parser.parse_args()

    data_dir = Path(args.data_dir).resolve()
    model_dir = Path(args.model_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    model_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    info = discover_datasets(str(data_dir))
    files_a, files_b = info["setA_files"], info["setB_files"]
    if not files_a or not files_b:
        raise FileNotFoundError(
            f"Expected .psv files in {data_dir / 'training_setA'} and {data_dir / 'training_setB'}"
        )
    if args.max_patients_per_set:
        files_a = files_a[:args.max_patients_per_set]
        files_b = files_b[:args.max_patients_per_set]

    print(f"Loading PhysioNet files: set A={len(files_a)}, set B={len(files_b)}")
    patients = process_files(files_a, "A") + process_files(files_b, "B")
    if len(patients) < 3:
        raise ValueError("At least 3 readable patient files are required.")

    ids = [str(frame["patient_id"].iloc[0]) for frame in patients]
    train_ids, val_ids, test_ids = split_patients_by_id(ids)
    train_set, val_set, test_set = set(train_ids), set(val_ids), set(test_ids)
    train_dfs = [p for p in patients if str(p["patient_id"].iloc[0]) in train_set]
    val_dfs = [p for p in patients if str(p["patient_id"].iloc[0]) in val_set]
    test_dfs = [p for p in patients if str(p["patient_id"].iloc[0]) in test_set]
    del patients

    feature_columns = get_feature_columns()
    print(f"Feature schema={FEATURE_SCHEMA_VERSION}; feature count={len(feature_columns)}")
    preprocessor = fit_preprocessor(train_dfs, feature_columns)
    X_train, y_train = apply_preprocessor(train_dfs, feature_columns, preprocessor)
    X_val, y_val = apply_preprocessor(val_dfs, feature_columns, preprocessor)
    X_test, y_test = apply_preprocessor(test_dfs, feature_columns, preprocessor)

    if len(np.unique(y_train)) < 2 or len(np.unique(y_val)) < 2:
        raise ValueError(
            "Train and validation splits must each contain both SepsisLabel classes. "
            "Use the full dataset rather than a tiny smoke-test subset."
        )

    print(f"Rows train/val/test: {len(y_train)}/{len(y_val)}/{len(y_test)}")
    print("Training models; hyperparameter search is confined to training data.")
    results = train_all_models(X_train, y_train, X_val, y_val)
    best_name, best_result = select_best_model(results, metric="pr_auc")
    if not best_name:
        raise RuntimeError("All model trainings failed. See errors above.")

    best_model = best_result["model"]
    val_probabilities = best_model.predict_proba(X_val)[:, 1]
    threshold = choose_f1_threshold(y_val, val_probabilities)
    test_probabilities = best_model.predict_proba(X_test)[:, 1]
    test_predictions = (test_probabilities >= threshold).astype(int)
    test_metrics = compute_metrics(y_test, test_predictions, test_probabilities)

    save_model(best_model, model_dir / "deterioration_model.pkl")
    save_preprocessor(preprocessor, model_dir / "preprocessing_pipeline.pkl")
    save_feature_columns(feature_columns, model_dir / "feature_columns.json")
    bands = risk_bands_from_validation(val_probabilities)
    (model_dir / "risk_thresholds.json").write_text(json.dumps(bands, indent=2), encoding="utf-8")

    comparison = {
        name: {
            "metrics": result.get("metrics", {}),
            "best_params": result.get("best_params", {}),
            "error": result.get("error"),
        }
        for name, result in results.items()
    }
    metadata = {
        "model_schema_version": FEATURE_SCHEMA_VERSION,
        "target": "SepsisLabel",
        "dataset": "PhysioNet Computing in Cardiology Challenge 2019",
        "selected_model": best_name,
        "selected_by": "validation PR-AUC",
        "feature_columns": feature_columns,
        "n_features": len(feature_columns),
        "patient_counts": {"train": len(train_ids), "validation": len(val_ids), "test": len(test_ids)},
        "row_counts": {"train": len(y_train), "validation": len(y_val), "test": len(y_test)},
        "validation_threshold_objective": "maximum F1 on validation split",
        "classification_threshold": threshold,
        "test_metrics": test_metrics,
        "risk_bands": bands["metadata"],
        "clinical_validation": False,
        "limitations": [
            "This predicts the PhysioNet SepsisLabel task, not general all-cause deterioration.",
            "The dataset is ICU-derived and does not establish performance in moving ambulances.",
            "Risk bands and classification threshold are research-prototype settings, not clinical triage rules.",
            "The model must not be used for autonomous treatment or destination decisions.",
        ],
    }
    (model_dir / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (output_dir / "model_comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    (output_dir / "test_metrics.json").write_text(json.dumps(test_metrics, indent=2), encoding="utf-8")

    print("\nModel comparison (validation):")
    for name, result in results.items():
        metrics = result.get("metrics", {})
        print(f"  {name}: PR-AUC={metrics.get('pr_auc')} F1={metrics.get('f1')} Recall={metrics.get('recall')}")
    print(f"Selected model: {best_name}")
    print(f"Validation-selected threshold: {threshold:.6f}")
    print(f"Held-out test metrics: {json.dumps(test_metrics, indent=2)}")
    print(f"Artifacts written to: {model_dir}")
    print("NOTE: prototype research model; not clinically validated.")


if __name__ == "__main__":
    main()

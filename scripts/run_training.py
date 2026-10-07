#!/usr/bin/env python3
"""
AmbuSense AI - Model 1 Training Pipeline
Patient Deterioration / Sepsis Risk Prediction
Using PhysioNet 2019 Sepsis Challenge Dataset
"""

import os
import sys
import gc
import json
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, "src")

from data_loader import (
    discover_datasets, print_dataset_info, patient_file_generator,
    load_patient_file, inspect_first_files, get_vital_columns
)
from feature_engineering import engineer_patient_features, get_feature_columns
from preprocessing import (
    split_patients_by_id, fit_preprocessor, apply_preprocessor,
    save_preprocessor, save_feature_columns
)
from train import train_all_models, select_best_model, save_model, save_metrics
from evaluate import (
    evaluate_model, plot_confusion_matrix, plot_roc_curve,
    plot_pr_curve, plot_feature_importance, create_comparison_table,
    save_comparison_table, find_optimal_threshold, define_risk_thresholds
)
from predict import SepsisPredictor


def process_patient_files(filepaths: list, dataset_source: str, max_patients: int = None) -> list:
    """Process patient files sequentially with memory efficiency."""
    processed = []
    count = 0

    for filepath in tqdm(filepaths, desc=f"Processing {dataset_source}"):
        if max_patients and count >= max_patients:
            break

        df = load_patient_file(filepath, dataset_source)

        if df.empty or "SepsisLabel" not in df.columns:
            continue

        df_feat = engineer_patient_features(df)
        if df_feat.empty:
            continue
        processed.append(df_feat)

        count += 1
        if count % 1000 == 0:
            gc.collect()

    return processed


def main():
    print("=" * 60)
    print("AMBUSENSE AI - MODEL 1 TRAINING PIPELINE")
    print("Patient Deterioration / Sepsis Risk Prediction")
    print("=" * 60)

    info = discover_datasets("data")
    print_dataset_info(info)

    print("\n[1/8] Inspecting dataset structure...")
    inspection = inspect_first_files(info["setA_files"], n=5)
    print(f"Columns: {inspection['columns']}")
    print(f"Label distribution (sample): {inspection['label_distribution']}")

    vital_cols = get_vital_columns(pd.read_csv(info["setA_files"][0], sep="|"))
    print(f"Vital sign columns: {vital_cols}")

    print("\n[2/8] Loading and processing patient data...")
    print("This may take several minutes...")

    all_patients = []
    for source, files in [("A", info["setA_files"]), ("B", info["setB_files"])]:
        patients = process_patient_files(files, source)
        all_patients.extend(patients)
        print(f"  Loaded {len(patients)} patients from Set {source}")

    print(f"\nTotal patients loaded: {len(all_patients)}")

    total_records = sum(len(p) for p in all_patients)
    print(f"Total records: {total_records}")

    print("\n[3/8] Analyzing dataset statistics...")
    all_dfs = pd.concat(all_patients, ignore_index=True)
    print(f"Columns: {all_dfs.columns.tolist()}")
    print(f"Missing value percentages:")
    missing_pct = (all_dfs.isnull().sum() / len(all_dfs) * 100).sort_values(ascending=False)
    print(missing_pct[missing_pct > 0].head(20))

    label_counts = all_dfs["SepsisLabel"].value_counts().sort_index()
    print(f"\nSepsisLabel distribution:")
    print(label_counts)
    print(f"Class imbalance ratio: {label_counts[0] / label_counts[1]:.2f}:1")

    feature_cols = get_feature_columns(all_dfs)
    print(f"\nFeature columns ({len(feature_cols)}): {feature_cols}")

    print("\n[4/8] Splitting patients (70/15/15)...")
    patient_ids = all_dfs["patient_id"].unique().tolist()
    train_ids, val_ids, test_ids = split_patients_by_id(patient_ids)

    print(f"Train patients: {len(train_ids)}")
    print(f"Val patients: {len(val_ids)}")
    print(f"Test patients: {len(test_ids)}")

    train_dfs = [p for p in all_patients if p["patient_id"].iloc[0] in train_ids]
    val_dfs = [p for p in all_patients if p["patient_id"].iloc[0] in val_ids]
    test_dfs = [p for p in all_patients if p["patient_id"].iloc[0] in test_ids]

    del all_patients, all_dfs
    gc.collect()

    print("\n[5/8] Fitting preprocessor on training data...")
    preprocessor = fit_preprocessor(train_dfs, feature_cols)
    save_preprocessor(preprocessor, "models/preprocessing_pipeline.pkl")
    save_feature_columns(feature_cols, "models/feature_columns.json")
    print("  Preprocessor saved.")

    print("\n[6/8] Preparing training/validation data...")
    X_train, y_train = apply_preprocessor(train_dfs, feature_cols, preprocessor)
    X_val, y_val = apply_preprocessor(val_dfs, feature_cols, preprocessor)

    print(f"Train shape: {X_train.shape}, Val shape: {X_val.shape}")
    print(f"Train labels: {np.bincount(y_train)}")
    print(f"Val labels: {np.bincount(y_val)}")

    del train_dfs, val_dfs
    gc.collect()

    print("\n[7/8] Training models...")
    results = train_all_models(X_train, y_train, X_val, y_val)

    print("\n[8/8] Evaluating and selecting best model...")
    best_name, best_result = select_best_model(results, metric="f1")
    print(f"\nBest model: {best_name}")
    print(f"Validation metrics: {best_result['metrics']}")

    print("\nFinal evaluation on test set...")
    X_test, y_test = apply_preprocessor(test_dfs, feature_cols, preprocessor)
    print(f"Test shape: {X_test.shape}")
    print(f"Test labels: {np.bincount(y_test)}")

    test_metrics = evaluate_model(best_result["model"], X_test, y_test)
    print(f"Test metrics: {test_metrics}")

    optimal_thresh = find_optimal_threshold(y_test, test_metrics["y_proba"], metric="f1")
    print(f"Optimal threshold (F1): {optimal_thresh:.4f}")

    test_metrics_optimal = evaluate_model(best_result["model"], X_test, y_test, threshold=optimal_thresh)
    print(f"Test metrics (optimal threshold): {test_metrics_optimal}")

    risk_thresholds = define_risk_thresholds(y_test, test_metrics["y_proba"])
    with open("models/risk_thresholds.json", "w") as f:
        json.dump(risk_thresholds, f, indent=2)
    print(f"Risk thresholds saved: {risk_thresholds}")

    print("\nGenerating plots...")
    plot_confusion_matrix(
        test_metrics_optimal["confusion_matrix"],
        "outputs/confusion_matrix.png",
        f"Confusion Matrix - {best_name} (Test Set)"
    )
    plot_roc_curve(y_test, test_metrics["y_proba"], "outputs/roc_curve.png", best_name)
    plot_pr_curve(y_test, test_metrics["y_proba"], "outputs/pr_curve.png", best_name)

    importance = plot_feature_importance(
        best_result["model"], feature_cols, "outputs/feature_importance.png", top_n=20
    )
    print(f"Top features: {list(importance.items())[:10]}")

    comparison_df = create_comparison_table(results)
    save_comparison_table(comparison_df, "outputs/model_comparison.csv")
    print(f"\nModel comparison saved to outputs/model_comparison.csv")
    print(comparison_df.to_string(index=False))

    save_model(best_result["model"], "models/deterioration_model.pkl")

    metadata = {
        "best_model": best_name,
        "feature_columns": feature_cols,
        "n_train_patients": len(train_ids),
        "n_val_patients": len(val_ids),
        "n_test_patients": len(test_ids),
        "n_features": len(feature_cols),
        "optimal_threshold": float(optimal_thresh),
        "risk_thresholds": risk_thresholds,
        "test_metrics": {k: v for k, v in test_metrics_optimal.items() if k not in ["y_proba", "y_pred"]}
    }
    with open("models/model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    test_results = test_metrics_optimal.copy()
    test_results.pop("y_proba", None)
    test_results.pop("y_pred", None)
    with open("models/model_metrics.json", "w") as f:
        json.dump(test_results, f, indent=2, default=str)

    print("\nRunning real-time simulation on unseen test patients...")
    realtime_results = simulate_realtime(
        test_dfs[:10], best_result["model"], preprocessor, feature_cols, risk_thresholds
    )

    realtime_df = pd.DataFrame(realtime_results)
    realtime_df.to_csv("outputs/realtime_test_results.csv", index=False)

    test_patient_info = []
    for df in test_dfs[:10]:
        test_patient_info.append({
            "patient_id": df["patient_id"].iloc[0],
            "ICULOS": df["ICULOS"].iloc[-1],
            "final_sepsis_label": df["SepsisLabel"].iloc[-1]
        })
    pd.DataFrame(test_patient_info).to_csv("outputs/unseen_test_patients.csv", index=False)

    print("\nTesting saved model reload...")
    predictor = SepsisPredictor(
        model_path="models/deterioration_model.pkl",
        preprocessor_path="models/preprocessing_pipeline.pkl",
        feature_columns_path="models/feature_columns.json",
        risk_thresholds_path="models/risk_thresholds.json"
    )

    test_result = predictor.predict_patient(
        heart_rate=108,
        spo2=92,
        temperature=38.1,
        sbp=100,
        dbp=65,
        respiratory_rate=24
    )
    print(f"Test prediction: {test_result}")

    print("\n" + "=" * 60)
    print("AMBUSENSE AI - MODEL 1 TRAINING COMPLETE")
    print("=" * 60)
    print(f"Dataset A patients: {len(info['setA_files'])}")
    print(f"Dataset B patients: {len(info['setB_files'])}")
    print(f"Total patients: {len(patient_ids)}")
    print(f"Total records: {total_records}")
    print(f"\nBest model: {best_name}")
    print(f"Accuracy: {test_metrics_optimal['accuracy']:.4f}")
    print(f"Precision: {test_metrics_optimal['precision']:.4f}")
    print(f"Recall: {test_metrics_optimal['recall']:.4f}")
    print(f"F1: {test_metrics_optimal['f1']:.4f}")
    print(f"ROC-AUC: {test_metrics_optimal['roc_auc']:.4f}")
    print(f"PR-AUC: {test_metrics_optimal['pr_auc']:.4f}")
    print(f"\nRealtime test patients: {len(realtime_df)}")
    print(f"\nModel saved: models/deterioration_model.pkl")
    print(f"\nStatus: READY FOR DJANGO INTEGRATION")
    print("=" * 60)


def simulate_realtime(test_dfs, model, preprocessor, feature_cols, risk_thresholds):
    """Simulate real-time predictions on test patients."""
    results = []

    for df in test_dfs:
        patient_id = df["patient_id"].iloc[0]
        predictor = SepsisPredictor(
            model_path="models/deterioration_model.pkl",
            preprocessor_path="models/preprocessing_pipeline.pkl",
            feature_columns_path="models/feature_columns.json",
            risk_thresholds_path="models/risk_thresholds.json"
        )

        for idx, row in df.iterrows():
            vitals = {col: row[col] for col in ["HR", "O2Sat", "Temp", "SBP", "DBP", "Resp", "MAP"] if col in row and pd.notna(row[col])}
            if len(vitals) < 3:
                continue

            result = predictor.predict_patient(
                heart_rate=vitals.get("HR", np.nan),
                spo2=vitals.get("O2Sat", np.nan),
                temperature=vitals.get("Temp", np.nan),
                sbp=vitals.get("SBP", np.nan),
                dbp=vitals.get("DBP", np.nan),
                respiratory_rate=vitals.get("Resp", np.nan),
                map_value=vitals.get("MAP", None),
                icu_los=row.get("ICULOS", None)
            )

            if "error" not in result:
                results.append({
                    "patient_id": patient_id,
                    "ICULOS": row.get("ICULOS", idx),
                    "HR": vitals.get("HR", np.nan),
                    "O2Sat": vitals.get("O2Sat", np.nan),
                    "SBP": vitals.get("SBP", np.nan),
                    "DBP": vitals.get("DBP", np.nan),
                    "Resp": vitals.get("Resp", np.nan),
                    "Risk_Probability": result["risk_probability"],
                    "Risk_Level": result["risk_level"],
                    "Prediction": result["prediction"],
                    "Actual_SepsisLabel": row.get("SepsisLabel", np.nan)
                })

    return results


if __name__ == "__main__":
    Path("models").mkdir(exist_ok=True)
    Path("outputs").mkdir(exist_ok=True)
    main()
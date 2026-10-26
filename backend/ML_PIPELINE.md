# LifeSyncAI ML pipeline (ambulance-compatible schema)

## Scope

The active Django application uses the code in `backend/`. The repository also contains older duplicate copies at the repository root; those are not the canonical runtime implementation.

The model compares three classifiers:
- Logistic Regression
- Random Forest
- XGBoost

The selected classifier is chosen by **validation PR-AUC**. A classification threshold is selected using **validation F1**. The held-out test split is evaluated only after these choices.

## Dataset

Use the PhysioNet Computing in Cardiology Challenge 2019 sepsis dataset. Obtain it from the official PhysioNet page and follow its access/credential requirements:

https://physionet.org/content/challenge-2019/1.0.0/

Put the extracted patient files into:

```text
backend/
  data/
    training_setA/*.psv
    training_setB/*.psv
```

Do not commit patient-level data files to Git.

## Feature contract

The runtime model is deliberately limited to variables available or manually entered in the current ambulance application:

- Age and Gender
- HR, Temp, SBP, DBP, Resp, MAP
- Previous value, change, rolling mean, rolling standard deviation, and short-window trend for each vital

MAP is derived as `(SBP + 2 * DBP) / 3` when SBP and DBP are available. Missing channels remain missing and are handled by the imputer fitted on training data. The code does not fabricate O2Sat, ECG, or laboratory values.

The same feature engineering implementation is used for offline training and online inference. Patient-level train/validation/test splitting and patient-grouped cross-validation are used to reduce leakage.

## Train the model

From the `backend` directory:

```bash
uv sync
uv run python scripts/run_training.py --data-dir data
```

The complete PhysioNet dataset can be memory- and CPU-intensive. For a small pipeline smoke test, run:

```bash
uv run python scripts/run_training.py --data-dir data --max-patients-per-set 100
```

A smoke-test subset may not contain both classes in every split and can correctly stop with a validation error. Do not use a subset-trained model as a project result.

Artifacts are written to `backend/models/`:
- `deterioration_model.pkl`
- `preprocessing_pipeline.pkl`
- `feature_columns.json`
- `risk_thresholds.json`
- `model_metadata.json`

Metrics and model comparisons are written to `backend/outputs/`.

## Runtime API behavior

The prediction endpoint requires `patient_id` so temporal history is not shared across patients. Age/Gender are read from the saved patient record if omitted from the request. Sensor channels may be null if unavailable, but each request must contain at least one vital measurement.

The runtime deliberately returns HTTP 503 when model artifacts are missing or use the legacy 114-feature schema. It does **not** convert inference errors into a fabricated LOW-risk response. After retraining, restart the Django server so the process loads the new artifacts.

Current ESP32 firmware reports heart rate and temperature only. BP and respiration must come from a supported sensor or manual entry before they can be treated as live sensor measurements. The dataset model's target is the PhysioNet `SepsisLabel`, not general all-cause deterioration.

## Clinical limitation

This is an educational/research prototype. ICU-derived PhysioNet data does not establish accuracy in a moving ambulance. Validation, calibration, prospective testing, and clinical review are required before any clinical use. Risk bands are prototype display bands, not validated triage thresholds. The system must not autonomously diagnose, prescribe treatment, or make destination decisions.

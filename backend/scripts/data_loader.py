import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Generator, Tuple, List, Optional
import gc
from tqdm import tqdm


def discover_datasets(base_path: str = "data") -> dict:
    """Discover training_setA and training_setB directories."""
    base = Path(base_path)
    setA = base / "training_setA"
    setB = base / "training_setB"

    result = {
        "setA_path": str(setA) if setA.exists() else None,
        "setB_path": str(setB) if setB.exists() else None,
        "setA_files": [],
        "setB_files": [],
    }

    if result["setA_path"]:
        result["setA_files"] = sorted([str(f) for f in setA.glob("*.psv") if f.suffix == ".psv"])
    if result["setB_path"]:
        result["setB_files"] = sorted([str(f) for f in setB.glob("*.psv") if f.suffix == ".psv"])

    return result


def print_dataset_info(info: dict):
    """Print dataset discovery information."""
    print("=" * 60)
    print("DATASET DISCOVERY")
    print("=" * 60)
    print(f"Dataset A path: {info['setA_path']}")
    print(f"Dataset B path: {info['setB_path']}")
    print(f"Number of files in A: {len(info['setA_files'])}")
    print(f"Number of files in B: {len(info['setB_files'])}")

    if not info["setA_path"] or not info["setB_path"]:
        print("\nERROR: Missing dataset(s)!")
        if not info["setA_path"]:
            print("  - training_setA not found")
        if not info["setB_path"]:
            print("  - training_setB not found")
        raise FileNotFoundError("Required dataset directories not found")


def load_patient_file(filepath: str, dataset_source: str) -> pd.DataFrame:
    """Load a single .psv patient file."""
    patient_id = Path(filepath).stem
    try:
        df = pd.read_csv(filepath, sep="|")
        if df.empty:
            return pd.DataFrame()
        df["patient_id"] = patient_id
        df["dataset_source"] = dataset_source
        return df
    except pd.errors.EmptyDataError:
        print(f"Warning: Empty file {filepath}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return pd.DataFrame()


def patient_file_generator(filepaths: List[str], dataset_source: str) -> Generator[pd.DataFrame, None, None]:
    """Memory-efficient generator yielding one patient DataFrame at a time."""
    for filepath in filepaths:
        df = load_patient_file(filepath, dataset_source)
        yield df
        del df
        gc.collect()


def inspect_first_files(filepaths: List[str], n: int = 3) -> dict:
    """Inspect first n files to determine columns and data characteristics."""
    all_columns = set()
    total_rows = 0
    label_counts = {0: 0, 1: 0}

    for i, filepath in enumerate(filepaths[:n]):
        df = pd.read_csv(filepath, sep="|")
        all_columns.update(df.columns)
        total_rows += len(df)
        if "SepsisLabel" in df.columns:
            label_counts[0] += (df["SepsisLabel"] == 0).sum()
            label_counts[1] += (df["SepsisLabel"] == 1).sum()

    return {
        "columns": sorted(list(all_columns)),
        "sample_rows": total_rows,
        "label_distribution": label_counts,
    }


def get_vital_columns(df: pd.DataFrame) -> List[str]:
    """Identify vital sign columns present in the data."""
    vital_candidates = ["HR", "O2Sat", "Temp", "SBP", "MAP", "DBP", "Resp"]
    return [col for col in vital_candidates if col in df.columns]


if __name__ == "__main__":
    info = discover_datasets()
    print_dataset_info(info)

    print("\nInspecting first 3 files from Set A...")
    inspection = inspect_first_files(info["setA_files"], n=3)
    print(f"Columns found: {inspection['columns']}")
    print(f"Sample rows: {inspection['sample_rows']}")
    print(f"Label distribution (first 3 files): {inspection['label_distribution']}")

    vitals = get_vital_columns(pd.read_csv(info["setA_files"][0], sep="|"))
    print(f"Vital sign columns present: {vitals}")
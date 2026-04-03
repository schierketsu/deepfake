#!/usr/bin/env python3
"""
Оценка сохранённой модели на train/test split того же CSV (как контроль воспроизводимости).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from ml.metadata_features import METADATA_FEATURE_NAMES  # noqa: E402


def main() -> int:
    csv_path = ROOT / "data" / "processed" / "features.csv"
    model_path = ROOT / "artifacts" / "model.joblib"
    if not csv_path.is_file():
        print(f"Нет {csv_path}")
        return 1
    if not model_path.is_file():
        print(f"Нет модели {model_path}. Запустите: python scripts/train_model.py")
        return 1

    df = pd.read_csv(csv_path)
    bundle = joblib.load(model_path)
    model = bundle["model"]
    feat_names = list(bundle.get("feature_names", METADATA_FEATURE_NAMES))

    X = df[feat_names].values.astype(np.float64)
    y = df["label"].values.astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    y_pred = model.predict(X_test)
    try:
        proba = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, proba)
    except Exception:
        auc = float("nan")

    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("Precision:", precision_score(y_test, y_pred, zero_division=0))
    print("Recall:", recall_score(y_test, y_pred, zero_division=0))
    print("F1:", f1_score(y_test, y_pred, zero_division=0))
    print("ROC-AUC:", auc)
    print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred, digits=4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

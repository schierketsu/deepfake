#!/usr/bin/env python3
# scaler+logreg по метафичам → model.joblib + training_metrics.json
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, classification_report, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.metadata_features import METADATA_FEATURE_NAMES  # noqa: E402


def main() -> int:
    csv_path = ROOT / "data" / "processed" / "features.csv"
    out_path = ROOT / "artifacts" / "model.joblib"
    metrics_path = ROOT / "artifacts" / "training_metrics.json"
    if not csv_path.is_file():
        print(f"Нет файла {csv_path}. Сначала: python scripts/build_dataset.py")
        return 1

    df = pd.read_csv(csv_path)
    if "label" not in df.columns or len(df) < 4:
        print("Недостаточно данных для обучения (нужно >= 4 строк и колонка label).")
        return 1

    missing = [c for c in METADATA_FEATURE_NAMES if c not in df.columns]
    if missing:
        print("Отсутствуют колонки признаков:", missing[:5], "...")
        return 1

    X = df[METADATA_FEATURE_NAMES].values.astype(np.float64)
    y = df["label"].values.astype(int)
    if len(np.unique(y)) < 2:
        print("Нужны оба класса (0 и 1) в label.")
        return 1

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    try:
        proba = model.predict_proba(X_test)[:, 1]
        auc = float(roc_auc_score(y_test, proba))
        ap = float(average_precision_score(y_test, proba))
    except Exception:
        auc = float("nan")
        ap = float("nan")

    f1 = float(f1_score(y_test, y_pred, zero_division=0))

    print(classification_report(y_test, y_pred, digits=4))
    print(f"ROC-AUC (holdout): {auc:.4f}")
    print(f"PR-AUC (holdout):  {ap:.4f}")

    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "data_csv": str(csv_path.relative_to(ROOT)),
        "n_total": int(len(df)),
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "random_state_split": 42,
        "test_size": 0.25,
        "roc_auc_holdout": auc,
        "pr_auc_holdout": ap,
        "f1_binary_holdout": f1,
        "feature_names": METADATA_FEATURE_NAMES,
        "model_type": "StandardScaler+LogisticRegression",
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": model,
        "feature_names": METADATA_FEATURE_NAMES,
        "metrics": metrics,
    }
    joblib.dump(bundle, out_path)
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"Сохранено: {out_path}")
    print(f"Метрики:   {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

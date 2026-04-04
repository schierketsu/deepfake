#!/usr/bin/env python3
# меряем сохранённую модель по мете; по умолчанию как train (holdout 0.25, seed 42)
# --json-out — отчёт в файл; --cv N — стратифицированный k-fold на всём csv
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split

from ml.metadata_features import METADATA_FEATURE_NAMES  # noqa: E402


def _run_holdout(df, model, feat_names: list[str]) -> dict:
    X = df[feat_names].values.astype(np.float64)
    y = df["label"].values.astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    # Модель уже обучена на полном train из прошлого шага — здесь оцениваем «как в train»:
    # переобучение на train split неверно. Стандарт: оценка на X_test без переобучения.
    y_pred = model.predict(X_test)
    try:
        proba = model.predict_proba(X_test)[:, 1]
        auc = float(roc_auc_score(y_test, proba))
        ap = float(average_precision_score(y_test, proba))
    except Exception:
        auc = float("nan")
        ap = float("nan")

    return {
        "mode": "holdout_same_split_as_train",
        "n_test": int(len(y_test)),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": auc,
        "pr_auc": ap,
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "classification_report": classification_report(y_test, y_pred, digits=4),
    }


def _run_cv(df, model, feat_names: list[str], n_splits: int) -> dict:
    X = df[feat_names].values.astype(np.float64)
    y = df["label"].values.astype(int)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    y_proba = cross_val_predict(
        model, X, y, cv=cv, method="predict_proba", n_jobs=1
    )[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)
    try:
        auc = float(roc_auc_score(y, y_proba))
        ap = float(average_precision_score(y, y_proba))
    except Exception:
        auc = float("nan")
        ap = float("nan")
    return {
        "mode": f"stratified_kfold_{n_splits}",
        "n_samples": int(len(y)),
        "accuracy": float(accuracy_score(y, y_pred)),
        "precision": float(precision_score(y, y_pred, zero_division=0)),
        "recall": float(recall_score(y, y_pred, zero_division=0)),
        "f1": float(f1_score(y, y_pred, zero_division=0)),
        "roc_auc": auc,
        "pr_auc": ap,
        "confusion_matrix": confusion_matrix(y, y_pred).tolist(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Оценка model.joblib на features.csv")
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="CSV признаков (по умолчанию data/processed/features.csv)",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=None,
        help="Путь к joblib (по умолчанию artifacts/model.joblib)",
    )
    parser.add_argument("--json-out", type=Path, default=None, help="Сохранить JSON-отчёт")
    parser.add_argument(
        "--cv",
        type=int,
        default=0,
        help="Если >0 — stratified K-fold CV на всём датасете (медленнее)",
    )
    args = parser.parse_args()

    csv_path = (args.csv or (ROOT / "data" / "processed" / "features.csv")).resolve()
    model_path = (args.model or (ROOT / "artifacts" / "model.joblib")).resolve()

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

    missing = [c for c in feat_names if c not in df.columns]
    if missing:
        print("В CSV нет колонок:", missing[:5])
        return 1

    if args.cv and args.cv > 1:
        report = _run_cv(df, model, feat_names, args.cv)
    else:
        report = _run_holdout(df, model, feat_names)

    printable = {k: v for k, v in report.items() if k != "classification_report"}
    print(json.dumps(printable, indent=2, ensure_ascii=False))
    if report.get("classification_report"):
        print(report["classification_report"])

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Записано: {args.json_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

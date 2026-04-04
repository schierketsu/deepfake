#!/usr/bin/env python3
"""
Сканирует data/raw/documents/real и data/raw/documents/ai, извлекает текст из .docx
и табличные признаки [`ml/docx_text_features.py`](../ml/docx_text_features.py) →
data/processed/docx_text_features.csv

Запуск из корня репозитория: python scripts/build_dataset_docx.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.docx_text import extract_plain_text_from_docx  # noqa: E402
from ml.docx_text_features import (  # noqa: E402
    DOCX_TEXT_FEATURE_NAMES,
    extract_docx_text_features,
)


def _collect_docx(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(folder.rglob("*")):
        if p.is_file() and p.suffix.lower() == ".docx":
            out.append(p)
    return out


def main() -> int:
    raw_real = ROOT / "data" / "raw" / "documents" / "real"
    raw_ai = ROOT / "data" / "raw" / "documents" / "ai"
    out_csv = ROOT / "data" / "processed" / "docx_text_features.csv"

    real_paths = _collect_docx(raw_real)
    ai_paths = _collect_docx(raw_ai)
    if not real_paths and not ai_paths:
        print(
            "Нет .docx в data/raw/documents/real и data/raw/documents/ai. "
            "Создайте папки и положите файлы или см. data/README.md"
        )
        return 1

    rows: list[dict] = []
    for p in real_paths:
        try:
            text = extract_plain_text_from_docx(str(p))
            feats = extract_docx_text_features(text)
            feats["label"] = 0
            feats["path"] = str(p.relative_to(ROOT))
            rows.append(feats)
        except Exception as e:
            print(f"skip {p}: {e}")
    for p in ai_paths:
        try:
            text = extract_plain_text_from_docx(str(p))
            feats = extract_docx_text_features(text)
            feats["label"] = 1
            feats["path"] = str(p.relative_to(ROOT))
            rows.append(feats)
        except Exception as e:
            print(f"skip {p}: {e}")

    if not rows:
        print("Не удалось извлечь ни одной строки.")
        return 1

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["path", "label"] + DOCX_TEXT_FEATURE_NAMES
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Записано {len(rows)} документов в {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Сканирует data/raw/real и data/raw/ai, для каждого изображения извлекает метаданные
(ImageAnalyzer) и табличные признаки **только из метаданных** → data/processed/features.csv.

Датасет по происхождению файла (класс 0/1), без признаков пикселей.
Запуск из корня репозитория: python scripts/build_dataset.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.services.image_analyzer import ImageAnalyzer  # noqa: E402
from ml.metadata_features import (  # noqa: E402
    METADATA_FEATURE_NAMES,
    extract_metadata_only_features,
)

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def _collect_images(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(folder.rglob("*")):
        if p.is_file() and p.suffix.lower() in IMAGE_EXT:
            out.append(p)
    return out


def main() -> int:
    raw_real = ROOT / "data" / "raw" / "real"
    raw_ai = ROOT / "data" / "raw" / "ai"
    out_csv = ROOT / "data" / "processed" / "features.csv"

    analyzer = ImageAnalyzer()
    real_paths = _collect_images(raw_real)
    ai_paths = _collect_images(raw_ai)
    if not real_paths and not ai_paths:
        print("Нет изображений в data/raw/real и data/raw/ai. См. data/README.md")
        return 1

    rows: list[dict] = []
    for p in real_paths:
        try:
            meta = analyzer.analyze(str(p))
            feats = extract_metadata_only_features(meta)
            feats["label"] = 0
            feats["path"] = str(p.relative_to(ROOT))
            rows.append(feats)
        except Exception as e:
            print(f"skip {p}: {e}")
    for p in ai_paths:
        try:
            meta = analyzer.analyze(str(p))
            feats = extract_metadata_only_features(meta)
            feats["label"] = 1
            feats["path"] = str(p.relative_to(ROOT))
            rows.append(feats)
        except Exception as e:
            print(f"skip {p}: {e}")

    if not rows:
        print("Не удалось извлечь ни одной строки.")
        return 1

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["path", "label"] + METADATA_FEATURE_NAMES
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Записано {len(rows)} строк (признаки только метаданных) в {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

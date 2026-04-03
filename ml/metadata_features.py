"""
Признаки только из результата ImageAnalyzer (метаданные EXIF/XMP/C2PA, без пикселей).

Датасет строится по **происхождению файла** (real vs AI), метка — в CSV;
модель учится отличать паттерны метаданных, а не «сюжет» изображения.
"""
from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional

import numpy as np

# Ключевые слова как в ImageAnalyzer / AIDetector (подсчёт вхождений в сериализованных метаданных)
_AI_KEYWORDS = (
    "stable diffusion",
    "midjourney",
    "dall-e",
    "dalle",
    "comfyui",
    "openai",
    "gpt",
    "generated",
    "ai generated",
    "neural",
    "diffusion",
    "c2pa",
    "algorithmic",
    "trainedalgorithmic",
)

STANDARD_AI_SIZES = {
    (512, 512),
    (768, 768),
    (1024, 1024),
    (512, 768),
    (768, 512),
    (1152, 896),
    (896, 1152),
    (1344, 768),
    (768, 1344),
    (1536, 640),
    (640, 1536),
    (1024, 1792),
    (1792, 1024),
}


def _flatten_meta_for_keywords(metadata: Dict[str, Any]) -> str:
    try:
        return json.dumps(metadata, ensure_ascii=False, default=str).lower()
    except Exception:
        return ""


def _count_ai_keyword_hits(text: str) -> float:
    if not text:
        return 0.0
    n = 0
    for kw in _AI_KEYWORDS:
        if kw in text:
            n += 1
    return float(min(n, 50))


METADATA_FEATURE_NAMES: List[str] = [
    "aspect_ratio",
    "log_width",
    "log_height",
    "is_square",
    "is_standard_ai_size",
    "has_gps",
    "has_camera",
    "has_shooting_params",
    "metadata_removed",
    "has_c2pa",
    "c2pa_algorithmic_hint",
    "c2pa_manifest_n",
    "c2pa_agent_len",
    "c2pa_generator_len",
    "exif_field_count",
    "software_str_len",
    "has_exif_flag",
    "has_xmp_flag",
    "contradictions_n",
    "ai_software_list_count",
    "suspicious_features_n",
    "metadata_keyword_hits",
    "metadata_trace_len_k",
]


def extract_metadata_only_features(metadata: Optional[Dict[str, Any]]) -> Dict[str, float]:
    """
    Вектор признаков из словаря ``ImageAnalyzer.analyze()`` (без чтения пикселей).
    """
    if not metadata or metadata.get("error"):
        return {name: 0.0 for name in METADATA_FEATURE_NAMES}

    ic = metadata.get("image_characteristics") or {}
    w = int(ic.get("width") or 0)
    h = int(ic.get("height") or 0)
    aspect = (w / h) if h else 1.0
    is_square = 1.0 if ic.get("is_square") else 0.0
    std_size = 1.0 if ic.get("is_standard_ai_size") else 0.0
    if (w, h) in STANDARD_AI_SIZES or (h, w) in STANDARD_AI_SIZES:
        std_size = 1.0

    exif = metadata.get("exif") or {}
    c2pa_meta = exif.get("_c2pa_metadata")
    if isinstance(c2pa_meta, dict) and len(c2pa_meta) > 0:
        has_c2pa = 1.0
        ds = str(c2pa_meta.get("c2pa_digital_source_type", "")).lower()
        c2pa_algorithmic = 1.0 if ("trained" in ds or "algorithmic" in ds) else 0.0
        sw_agent_len = len(str(c2pa_meta.get("c2pa_software_agent", "")))
        gen_len = len(str(c2pa_meta.get("c2pa_generator_name", "")))
    else:
        has_c2pa = 1.0 if (exif.get("_c2pa_manifest_types") or exif.get("_c2pa_metadata")) else 0.0
        c2pa_algorithmic = 0.0
        sw_agent_len = 0
        gen_len = 0

    manifest_types = exif.get("_c2pa_manifest_types") or []
    if isinstance(manifest_types, list):
        c2pa_manifest_n = float(min(len(manifest_types), 50))
    else:
        c2pa_manifest_n = 0.0

    exif_count = 0.0
    if isinstance(exif.get("_grouped_metadata"), dict):
        for _k, rows in exif["_grouped_metadata"].items():
            if isinstance(rows, list):
                exif_count += len(rows)
    else:
        exif_count = float(len([k for k in exif.keys() if not str(k).startswith("_")]))

    software = str(exif.get("software", "") or "")
    software_len = float(min(len(software), 2000))

    integrity = metadata.get("metadata_integrity") or {}
    meta_removed = 1.0 if integrity.get("metadata_removed") else 0.0
    has_exif = 1.0 if integrity.get("has_exif") else 0.0
    has_xmp = 1.0 if integrity.get("has_xmp") else 0.0
    contradictions_n = float(min(len(integrity.get("contradictions") or []), 20))

    ai_sw = metadata.get("ai_software_detected") or []
    ai_sw_count = float(min(len(ai_sw), 50))

    susp = ic.get("suspicious_features") or []
    suspicious_n = float(min(len(susp), 50))

    flat = _flatten_meta_for_keywords(metadata)
    keyword_hits = _count_ai_keyword_hits(flat)

    # Длина «следа» в символах (очень грубый proxy богатства метаданных)
    trace_len = float(min(len(flat), 100_000)) / 1000.0

    return {
        "aspect_ratio": float(aspect),
        "log_width": float(math.log1p(max(w, 0))),
        "log_height": float(math.log1p(max(h, 0))),
        "is_square": is_square,
        "is_standard_ai_size": std_size,
        "has_gps": 1.0 if ic.get("has_gps") else 0.0,
        "has_camera": 1.0 if ic.get("has_camera_info") else 0.0,
        "has_shooting_params": 1.0 if ic.get("has_shooting_params") else 0.0,
        "metadata_removed": meta_removed,
        "has_c2pa": has_c2pa,
        "c2pa_algorithmic_hint": c2pa_algorithmic,
        "c2pa_manifest_n": c2pa_manifest_n,
        "c2pa_agent_len": float(min(sw_agent_len, 2000)),
        "c2pa_generator_len": float(min(gen_len, 2000)),
        "exif_field_count": min(exif_count, 5000.0),
        "software_str_len": software_len,
        "has_exif_flag": has_exif,
        "has_xmp_flag": has_xmp,
        "contradictions_n": contradictions_n,
        "ai_software_list_count": ai_sw_count,
        "suspicious_features_n": suspicious_n,
        "metadata_keyword_hits": keyword_hits,
        "metadata_trace_len_k": trace_len,
    }


def vectorize_metadata_features(
    combined: Dict[str, float],
    names: Optional[List[str]] = None,
) -> np.ndarray:
    names = names or METADATA_FEATURE_NAMES
    return np.array([combined.get(n, 0.0) for n in names], dtype=np.float64)

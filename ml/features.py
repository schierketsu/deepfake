"""
Опциональные **пиксельные** признаки (эксперименты). Основной пайплайн проекта — только метаданные:
см. :mod:`ml.metadata_features` и :func:`ml.inference.predict_metadata_ml_score`.
"""
from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

try:
    from skimage import filters
    from skimage.util import img_as_float
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False


FEATURE_NAMES: List[str] = [
    "mean_r",
    "mean_g",
    "mean_b",
    "std_r",
    "std_g",
    "std_b",
    "gray_mean",
    "gray_std",
    "entropy_gray",
    "laplacian_var",
    "fft_energy_high",
    "fft_energy_mid",
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
    "exif_field_count",
]


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


def _entropy_from_hist(gray: np.ndarray) -> float:
    """Shannon entropy of normalized intensity histogram."""
    g = gray.astype(np.float64).ravel()
    g = np.clip(g, 0.0, 255.0)
    hist, _ = np.histogram(g, bins=64, range=(0, 255), density=True)
    hist = hist[hist > 0]
    return float(-np.sum(hist * np.log2(hist + 1e-12)))


def extract_visual_features_from_array(rgb: np.ndarray) -> Dict[str, float]:
    """Признаки из RGB массива uint8 (H, W, 3)."""
    if rgb.ndim != 3 or rgb.shape[2] < 3:
        raise ValueError("Expected RGB image (H, W, 3)")
    r = rgb[:, :, 0].astype(np.float64)
    g = rgb[:, :, 1].astype(np.float64)
    b = rgb[:, :, 2].astype(np.float64)
    gray = 0.299 * r + 0.587 * g + 0.114 * b

    feats: Dict[str, float] = {
        "mean_r": float(np.mean(r)),
        "mean_g": float(np.mean(g)),
        "mean_b": float(np.mean(b)),
        "std_r": float(np.std(r)),
        "std_g": float(np.std(g)),
        "std_b": float(np.std(b)),
        "gray_mean": float(np.mean(gray)),
        "gray_std": float(np.std(gray)),
        "entropy_gray": _entropy_from_hist(gray),
    }

    if HAS_SKIMAGE:
        gray_f = img_as_float(gray)
        feats["laplacian_var"] = float(np.var(filters.laplace(gray_f)))
        # FFT radial energy bands (simplified)
        fft = np.fft.rfft2(gray_f)
        ps = np.abs(fft) ** 2
        h, w = ps.shape
        cy, cx = h // 2, min(w - 1, w // 2)
        y, x = np.ogrid[:h, :w]
        r = np.sqrt((y - cy) ** 2 + (x - cx) ** 2)
        r_max = max(r.max(), 1e-6)
        high = ps[r > 0.5 * r_max].sum()
        mid = ps[(r > 0.25 * r_max) & (r <= 0.5 * r_max)].sum()
        total = ps.sum() + 1e-12
        feats["fft_energy_high"] = float(high / total)
        feats["fft_energy_mid"] = float(mid / total)
    else:
        feats["laplacian_var"] = float(np.var(np.gradient(gray)[0]) + np.var(np.gradient(gray)[1]))
        feats["fft_energy_high"] = 0.0
        feats["fft_energy_mid"] = 0.0

    return feats


def extract_metadata_feature_vector(metadata: Optional[Dict[str, Any]]) -> Dict[str, float]:
    """Бинарные и счётные признаки из результата ImageAnalyzer."""
    if not metadata:
        return {
            "aspect_ratio": 1.0,
            "log_width": 0.0,
            "log_height": 0.0,
            "is_square": 0.0,
            "is_standard_ai_size": 0.0,
            "has_gps": 0.0,
            "has_camera": 0.0,
            "has_shooting_params": 0.0,
            "metadata_removed": 1.0,
            "has_c2pa": 0.0,
            "exif_field_count": 0.0,
        }

    ic = metadata.get("image_characteristics") or {}
    w = ic.get("width") or 0
    h = ic.get("height") or 0
    aspect = (w / h) if h else 1.0
    is_square = 1.0 if ic.get("is_square") else 0.0
    std_size = 1.0 if ic.get("is_standard_ai_size") else 0.0
    if (w, h) in STANDARD_AI_SIZES or (h, w) in STANDARD_AI_SIZES:
        std_size = 1.0

    exif = metadata.get("exif") or {}
    has_c2pa = 1.0 if (exif.get("_c2pa_metadata") or exif.get("_c2pa_manifest_types")) else 0.0
    exif_count = 0.0
    if isinstance(exif.get("_grouped_metadata"), dict):
        for _k, rows in exif["_grouped_metadata"].items():
            if isinstance(rows, list):
                exif_count += len(rows)
    else:
        exif_count = float(len([k for k in exif.keys() if not str(k).startswith("_")]))

    integrity = metadata.get("metadata_integrity") or {}
    meta_removed = 1.0 if integrity.get("metadata_removed") else 0.0

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
        "exif_field_count": min(exif_count, 5000.0),
    }


def combine_feature_dicts(visual: Dict[str, float], meta_vec: Dict[str, float]) -> Dict[str, float]:
    out = dict(visual)
    out.update(meta_vec)
    return out


def vectorize_features(combined: Dict[str, float], names: Optional[List[str]] = None) -> np.ndarray:
    names = names or FEATURE_NAMES
    return np.array([combined.get(n, 0.0) for n in names], dtype=np.float64)


def extract_all_features(image_path: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, float], List[str]]:
    """
    Полный вектор признаков для одного изображения.
    Возвращает (dict, ordered_names).
    """
    metadata = metadata or {}
    with Image.open(image_path) as im:
        im = im.convert("RGB")
        rgb = np.array(im)
    visual = extract_visual_features_from_array(rgb)
    meta_vec = extract_metadata_feature_vector(metadata)
    combined = combine_feature_dicts(visual, meta_vec)
    return combined, FEATURE_NAMES


def load_image_rgb(image_path: str, max_side: int = 1024) -> np.ndarray:
    """Загрузка и при необходимости даунскейл для скорости."""
    with Image.open(image_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        if max(w, h) > max_side:
            scale = max_side / float(max(w, h))
            im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        return np.array(im)

"""
Инференс sklearn-модели по признакам текста DOCX → оценка 0–100 (класс 1 = «ai» в датасете).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import joblib
except ImportError:
    joblib = None  # type: ignore

from ml.docx_text_features import (
    DOCX_TEXT_FEATURE_NAMES,
    extract_docx_text_features,
    vectorize_docx_text_features,
)

_model = None
_model_path: Optional[str] = None
_feature_names: Optional[List[str]] = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_docx_model_path() -> Path:
    env = os.environ.get("ML_DOCX_MODEL_PATH")
    if env:
        return Path(env)
    return _repo_root() / "artifacts" / "model_docx.joblib"


def load_docx_model(path: Optional[Path] = None) -> Tuple[Any, List[str]]:
    global _model, _model_path, _feature_names
    path = path or default_docx_model_path()
    path = path.resolve()
    if joblib is None:
        raise RuntimeError("joblib is required for ML inference")
    if not path.is_file():
        raise FileNotFoundError(f"DOCX NLP model not found: {path}")
    if _model is not None and str(_model_path) == str(path):
        return _model, _feature_names or DOCX_TEXT_FEATURE_NAMES

    bundle = joblib.load(path)
    if isinstance(bundle, dict) and "model" in bundle:
        _model = bundle["model"]
        _feature_names = list(bundle.get("feature_names", DOCX_TEXT_FEATURE_NAMES))
    else:
        _model = bundle
        _feature_names = list(DOCX_TEXT_FEATURE_NAMES)

    _model_path = str(path)
    return _model, _feature_names


def is_docx_model_available(path: Optional[Path] = None) -> bool:
    p = path or default_docx_model_path()
    return p.is_file() and joblib is not None


def predict_docx_nlp_score(
    plain_text: Optional[str],
    model_path: Optional[Path] = None,
) -> Tuple[Optional[int], bool, Dict[str, Any]]:
    """
    Вероятность класса «ai» по текстовым признакам, 0–100.
    """
    debug: Dict[str, Any] = {"model_path": str(model_path or default_docx_model_path())}
    if joblib is None:
        debug["error"] = "joblib not installed"
        return None, False, debug

    path = model_path or default_docx_model_path()
    if not path.is_file():
        debug["error"] = "model file missing"
        return None, False, debug

    text = (plain_text or "").strip()
    if not text:
        debug["error"] = "empty document text"
        return None, False, debug

    try:
        model, feat_names = load_docx_model(path)
    except Exception as e:
        debug["error"] = str(e)
        return None, False, debug

    try:
        combined = extract_docx_text_features(text)
        X = vectorize_docx_text_features(combined, feat_names).reshape(1, -1)
    except Exception as e:
        debug["error"] = f"features: {e}"
        return None, False, debug

    try:
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
            if proba.shape[0] >= 2:
                score = int(round(float(proba[1]) * 100))
            else:
                score = int(round(float(proba[0]) * 100))
        else:
            pred = model.predict(X)[0]
            score = int(round(float(pred) * 100)) if pred <= 1.0 else int(pred)
        score = max(0, min(100, score))
        debug["ok"] = True
        return score, True, debug
    except Exception as e:
        debug["error"] = str(e)
        return None, False, debug


def clear_docx_model_cache() -> None:
    global _model, _model_path, _feature_names
    _model = None
    _model_path = None
    _feature_names = None

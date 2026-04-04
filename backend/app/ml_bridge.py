"""
Подключение пакета ``ml`` из корня репозитория (рядом с ``backend/``).
"""
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def predict_metadata_ml_safe(
    metadata: Optional[Dict[str, Any]],
) -> Tuple[Optional[int], bool]:
    """ML по признакам метаданных (без пикселей). Не падает при отсутствии модели."""
    try:
        from ml.inference import predict_metadata_ml_score

        score, ok, _dbg = predict_metadata_ml_score(metadata)
        return score, ok
    except Exception:
        return None, False


def predict_visual_score_safe(
    image_path: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[int], bool]:
    """Устарело: используйте predict_metadata_ml_safe(metadata); image_path игнорируется."""
    return predict_metadata_ml_safe(metadata)


def extract_docx_plain_text_safe(path: str) -> str:
    """Текст DOCX для NLP-слоя. Пустая строка при ошибке."""
    try:
        from ml.docx_text import extract_plain_text_from_docx

        return extract_plain_text_from_docx(path) or ""
    except Exception:
        return ""


def predict_docx_nlp_safe(plain_text: Optional[str]) -> Tuple[Optional[int], bool]:
    """ML по статистике текста документа (отдельная модель model_docx.joblib)."""
    try:
        from ml.inference_docx import predict_docx_nlp_score

        score, ok, _dbg = predict_docx_nlp_score(plain_text)
        return score, ok
    except Exception:
        return None, False

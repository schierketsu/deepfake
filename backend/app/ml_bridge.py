# кладём корень репы в path чтобы импортить ml
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def predict_metadata_ml_safe(
    metadata: Optional[Dict[str, Any]],
) -> Tuple[Optional[int], bool]:
    # ml по мете, без модели просто none/false
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
    # старое api, путь к файлу не нужен
    return predict_metadata_ml_safe(metadata)


def extract_docx_plain_text_safe(path: str) -> str:
    # сырой текст docx для nlp; косяк → ""
    try:
        from ml.docx_text import extract_plain_text_from_docx

        return extract_plain_text_from_docx(path) or ""
    except Exception:
        return ""


def predict_docx_nlp_safe(plain_text: Optional[str]) -> Tuple[Optional[int], bool]:
    # отдельная модель по текстовым фичам docx
    try:
        from ml.inference_docx import predict_docx_nlp_score

        score, ok, _dbg = predict_docx_nlp_score(plain_text)
        return score, ok
    except Exception:
        return None, False

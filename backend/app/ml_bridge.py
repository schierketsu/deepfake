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

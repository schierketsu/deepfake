"""
Слияние оценок: эвристика по метаданным (baseline) + ML **только по табличным признакам метаданных**.

При наличии сильных фактов C2PA/Content Credentials приоритет у metadata_score.
Если ML-модель недоступна, итог совпадает с metadata_score.
"""
from typing import Any, Dict, Optional, Tuple


def has_strong_c2pa_evidence(ai_result: Dict[str, Any]) -> bool:
    """True, если есть убедительные факты из C2PA в evidence_from_metadata."""
    evidence = ai_result.get("evidence_from_metadata") or []
    if evidence:
        return True
    software = ai_result.get("software_detected") or []
    return any("C2PA" in str(s) for s in software)


def fuse_image_scores(
    metadata_score: int,
    ml_metadata_score: Optional[int],
    ai_result: Dict[str, Any],
    metadata_ml_available: bool,
    weight_heuristic: float = 0.35,
    weight_ml: float = 0.65,
) -> Tuple[int, str]:
    """
    Возвращает (final_score_0_100, fusion_method).

    - При сильном C2PA: итог ближе к эвристике; ML по метаданным слегка корректирует.
    - При доступной ML-модели на метаданных: взвешенное среднее эвристики и ML.
    - Без модели: только metadata_score.
    """
    meta = max(0, min(100, int(metadata_score)))

    if has_strong_c2pa_evidence(ai_result):
        if metadata_ml_available and ml_metadata_score is not None:
            v = max(0, min(100, int(ml_metadata_score)))
            fused = int(round(0.85 * meta + 0.15 * v))
            return min(100, fused), "c2pa_priority_blend"

    if not metadata_ml_available or ml_metadata_score is None:
        return meta, "metadata_only"

    v = max(0, min(100, int(ml_metadata_score)))
    fused = int(round(weight_heuristic * meta + weight_ml * v))
    return min(100, max(0, fused)), "weighted_heuristic_ml_metadata"

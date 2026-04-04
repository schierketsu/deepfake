# склеиваем эвристику по мете и ml по табличным метафичам; c2pa жёстче тянет к эвристике
from typing import Any, Dict, Optional, Tuple


def has_strong_c2pa_evidence(ai_result: Dict[str, Any]) -> bool:
    # явные c2pa-доказательства в evidence или в software
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
    # (итог 0–100, метка способа): c2pa → в основном эвристика; иначе blend или только мета
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

from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class Summary(BaseModel):
    location: Optional[str] = None
    date_time: Optional[str] = None
    source: Optional[str] = None
    ai_probability: int  # 0-100 итог (после слияния)
    confidence: str  # "high", "medium", "low"
    metadata_score: Optional[int] = None
    ml_metadata_score: Optional[int] = None
    final_score: Optional[int] = None
    metadata_ml_available: Optional[bool] = None
    # Отдельная модель по тексту DOCX (см. ml/docx_text_features, artifacts/model_docx.joblib)
    doc_nlp_ml_score: Optional[int] = None
    doc_nlp_ml_available: Optional[bool] = None

class AIMetadata(BaseModel):
    software_detected: List[str]
    heuristics: Dict[str, Any]
    anomalies: List[str]
    evidence_from_metadata: Optional[List[str]] = None  # Факты из C2PA/метаданных
    # Эвристика по метаданным + ML по табличным признакам метаданных (см. score_fusion)
    metadata_score: Optional[int] = None
    ml_metadata_score: Optional[int] = None
    final_score: Optional[int] = None
    metadata_ml_available: Optional[bool] = None
    fusion_method: Optional[str] = None

class AnalysisResponse(BaseModel):
    file_type: str  # "document" (DOCX/PPTX)
    summary: Summary
    metadata: Dict[str, Any]
    ai_indicators: AIMetadata
    report_url: str

from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class Summary(BaseModel):
    location: Optional[str] = None
    date_time: Optional[str] = None
    source: Optional[str] = None
    ai_probability: int  # 0-100
    confidence: str  # "high", "medium", "low"

class AIMetadata(BaseModel):
    software_detected: List[str]
    heuristics: Dict[str, Any]
    anomalies: List[str]
    evidence_from_metadata: Optional[List[str]] = None  # Факты из C2PA/метаданных

class AnalysisResponse(BaseModel):
    file_type: str  # "document" (DOCX/PPTX)
    summary: Summary
    metadata: Dict[str, Any]
    ai_indicators: AIMetadata
    report_url: str

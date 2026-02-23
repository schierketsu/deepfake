from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import tempfile
import logging
from app.services.document_analyzer import DocumentAnalyzer
from app.services.report_generator import ReportGenerator, REPORTS_DIR
from app.models.schemas import AnalysisResponse, Summary, AIMetadata

logger = logging.getLogger(__name__)

router = APIRouter()

# Максимальный размер файла: 100MB
MAX_FILE_SIZE = 100 * 1024 * 1024

@router.get("/health")
async def health_check():
    """Проверка статуса сервиса"""
    return {"status": "ok", "service": "deepfake-metadata-analyzer"}


@router.get("/routes")
async def list_routes():
    """Список доступных эндпоинтов (только офисные файлы DOCX/PPTX)"""
    return {
        "endpoints": [
            "GET /api/health",
            "GET /api/routes",
            "POST /api/analyze/document",
            "GET /api/reports/{filename}",
        ]
    }


@router.post("/analyze/document", response_model=AnalysisResponse)
@router.post("/analyze/document/", response_model=AnalysisResponse)
async def analyze_document(file: UploadFile = File(...)):
    """
    Анализ офисного документа DOCX/PPTX: извлечение метаданных и проверка встроенных изображений.
    """
    temp_file = None
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Файл слишком большой (максимум 100MB)")

        fn = (file.filename or "").lower()
        if not (fn.endswith(".docx") or fn.endswith(".pptx")):
            raise HTTPException(
                status_code=400,
                detail="Поддерживаются только форматы DOCX и PPTX",
            )

        suffix = ".pptx" if fn.endswith(".pptx") else ".docx"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            temp_file = tmp.name

        doc_analyzer = DocumentAnalyzer()
        doc_result = doc_analyzer.analyze_document(temp_file)

        doc_type = doc_result.get("document_type", "word")
        doc_label = "PowerPoint" if doc_type == "powerpoint" else "Word"
        document_metadata = doc_result.get("document_metadata", {})
        embedded_images = doc_result.get("embedded_images", [])
        images_count = doc_result["images_count"]
        if images_count == 0:
            summary = Summary(
                location=None,
                date_time=None,
                source=f"{doc_label} документ (изображений не найдено)",
                ai_probability=0,
                confidence="low",
            )
            report_data = {
                "file_type": "document",
                "summary": {
                    "location": None,
                    "date_time": None,
                    "source": f"{doc_label} документ (изображений не найдено)",
                    "ai_probability": 0,
                    "confidence": "low",
                },
                "metadata": {
                    "document_type": doc_type,
                    "document_metadata": document_metadata,
                    "embedded_images": embedded_images,
                    "images": [],
                    "images_count": 0,
                    "images_with_ai_count": 0,
                },
                "ai_indicators": {
                    "software_detected": [],
                    "heuristics": {},
                    "anomalies": [],
                    "evidence_from_metadata": [],
                },
                "file_info": {
                    "name": file.filename or f"document{suffix}",
                    "size": len(content),
                    "size_formatted": f"{len(content) / 1024:.2f} KB",
                },
                "generated_at": __import__("datetime").datetime.now().isoformat(),
            }
            report_gen = ReportGenerator()
            report_path = report_gen.generate_pdf_report(report_data, temp_file)
        else:
            agg = doc_result["aggregated"]
            summary = Summary(
                location=None,
                date_time=None,
                source=f"{doc_label} документ: изображений {images_count}, с признаками ИИ — {doc_result['images_with_ai_count']}",
                ai_probability=agg["ai_probability"],
                confidence=agg["confidence"],
            )
            report_gen = ReportGenerator()
            report_data = {
                "file_type": "document",
                "summary": {
                    "location": None,
                    "date_time": None,
                    "source": f"{doc_label} документ: изображений {images_count}, с признаками ИИ — {doc_result['images_with_ai_count']}",
                    "ai_probability": agg["ai_probability"],
                    "confidence": agg["confidence"],
                },
                "metadata": {
                    "document_type": doc_type,
                    "document_metadata": document_metadata,
                    "embedded_images": embedded_images,
                    "images": doc_result["images"],
                    "images_count": images_count,
                    "images_with_ai_count": doc_result["images_with_ai_count"],
                },
                "ai_indicators": {
                    "software_detected": agg["software_detected"],
                    "heuristics": {},
                    "anomalies": agg["anomalies"],
                    "evidence_from_metadata": agg["evidence_from_metadata"],
                },
                "file_info": {
                    "name": file.filename or f"document{suffix}",
                    "size": len(content),
                    "size_formatted": f"{len(content) / (1024*1024):.2f} MB" if len(content) >= 1024 * 1024 else f"{len(content) / 1024:.2f} KB",
                },
            }
            report_data["generated_at"] = __import__("datetime").datetime.now().isoformat()
            report_gen = ReportGenerator()
            report_path = report_gen.generate_pdf_report(report_data, temp_file)

        report_filename = os.path.basename(report_path)
        if not os.path.exists(report_path):
            logger.error("PDF отчёт не создан: %s", report_path)
            raise HTTPException(status_code=500, detail="Не удалось создать PDF-отчёт")

        return AnalysisResponse(
            file_type="document",
            summary=summary,
            metadata=report_data["metadata"],
            ai_indicators=AIMetadata(
                software_detected=report_data["ai_indicators"]["software_detected"],
                heuristics=report_data["ai_indicators"].get("heuristics", {}),
                anomalies=report_data["ai_indicators"].get("anomalies", []),
                evidence_from_metadata=report_data["ai_indicators"].get("evidence_from_metadata") or [],
            ),
            report_url=f"/api/reports/{report_filename}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Ошибка анализа документа: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка анализа документа: {str(e)}")
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)


@router.get("/reports/{report_filename}")
async def get_report(report_filename: str):
    """Получение PDF отчета"""
    report_path = os.path.join(REPORTS_DIR, report_filename)
    
    if not os.path.exists(report_path):
        logger.warning("Отчёт не найден: %s (каталог: %s)", report_path, REPORTS_DIR)
        raise HTTPException(status_code=404, detail="Отчет не найден")
    
    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=report_filename
    )

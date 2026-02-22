from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
import os
import tempfile
import subprocess
import logging
import time
from app.services.image_analyzer import ImageAnalyzer
from app.services.video_analyzer import VideoAnalyzer
from app.services.ai_detector import AIDetector
from app.services.document_analyzer import DocumentAnalyzer
from app.services.report_generator import ReportGenerator
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
    """Список доступных эндпоинтов (для проверки)"""
    return {
        "endpoints": [
            "GET /api/health",
            "GET /api/routes",
            "POST /api/analyze/image",
            "POST /api/analyze/video",
            "POST /api/analyze/document",
            "GET /api/reports/{filename}",
        ]
    }

@router.get("/test/exiftool")
async def test_exiftool():
    """Тестовая проверка работы ExifTool"""
    from app.services.image_analyzer import ImageAnalyzer
    import os
    
    analyzer = ImageAnalyzer()
    
    result = {
        "exiftool_available": analyzer._check_exiftool_available(),
        "exiftool_command": None,
        "paths_checked": analyzer._get_exiftool_paths(),
        "test_result": None,
        "error": None
    }
    
    if result["exiftool_available"]:
        result["exiftool_command"] = analyzer._get_exiftool_command()
        
        # Пробуем выполнить простую команду
        try:
            import subprocess
            test_result = subprocess.run(
                [result["exiftool_command"], '-ver'],
                capture_output=True,
                text=True,
                timeout=5
            )
            result["test_result"] = {
                "returncode": test_result.returncode,
                "stdout": test_result.stdout.strip(),
                "stderr": test_result.stderr.strip()
            }
        except Exception as e:
            result["error"] = str(e)
    
    return result

@router.post("/analyze/image", response_model=AnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    Анализ метаданных изображения
    
    Поддерживаемые форматы: JPEG, PNG, HEIC, HEIF
    """
    # Создание временного файла
    temp_file = None
    try:
        content = await file.read()
        
        # Валидация размера файла
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Файл слишком большой (максимум 100MB)")
        
        # Валидация MIME типа (допускаем также по расширению, т.к. content_type иногда пустой или нестандартный)
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/heic", "image/heif"]
        fn = (file.filename or "").lower()
        allowed_extensions = (".jpg", ".jpeg", ".png", ".heic", ".heif")
        if file.content_type not in allowed_types and not any(fn.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=400, 
                detail=f"Неподдерживаемый тип файла. Разрешены: JPEG, JPG, PNG, HEIC, HEIF"
            )
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            tmp.write(content)
            temp_file = tmp.name
        
        start_time = time.time()
        logger.info(f"Начало анализа изображения: {file.filename}, размер: {len(content)} байт")
        
        try:
            # Анализ изображения
            analyzer_start = time.time()
            analyzer = ImageAnalyzer()
            logger.info("Запуск анализа метаданных изображения...")
            metadata = analyzer.analyze(temp_file)
            analyzer_time = time.time() - analyzer_start
            logger.info(f"✓ Анализ метаданных завершен за {analyzer_time:.2f} сек")
            
            # Детекция ИИ
            detector_start = time.time()
            ai_detector = AIDetector()
            logger.info("Запуск детекции ИИ...")
            ai_indicators = ai_detector.detect_ai_signs(metadata, file_type="image")
            detector_time = time.time() - detector_start
            logger.info(f"✓ Детекция ИИ завершена за {detector_time:.2f} сек")
            
            # Генерация отчета
            report_start = time.time()
            report_gen = ReportGenerator()
            logger.info("Генерация отчета...")
            report_data = report_gen.format_analysis_result(
                file_type="image",
                metadata=metadata,
                ai_indicators=ai_indicators
            )
            
            # Добавляем информацию о файле
            file_size_mb = len(content) / (1024 * 1024)
            report_data["file_info"] = {
                "name": file.filename or "Неизвестно",
                "size": len(content),
                "size_formatted": f"{file_size_mb:.2f} MB" if file_size_mb >= 1 else f"{len(content) / 1024:.2f} KB"
            }
            
            # Генерация PDF отчета
            report_path = report_gen.generate_pdf_report(report_data, temp_file)
            report_time = time.time() - report_start
            logger.info(f"✓ Генерация отчета завершена за {report_time:.2f} сек")
            
            total_time = time.time() - start_time
            logger.info(f"✓ Анализ изображения полностью завершен за {total_time:.2f} сек")
            
            return AnalysisResponse(
                file_type="image",
                summary=report_data["summary"],
                metadata=report_data["metadata"],
                ai_indicators={
                    "software_detected": ai_indicators.get("software_detected", []),
                    "heuristics": ai_indicators.get("heuristics", {}),
                    "anomalies": ai_indicators.get("anomalies", []),
                    "evidence_from_metadata": ai_indicators.get("evidence_from_metadata") or [],
                },
                report_url=f"/api/reports/{os.path.basename(report_path)}"
            )
        except subprocess.TimeoutExpired as e:
            logger.error(f"Таймаут при анализе изображения: {e}")
            raise HTTPException(status_code=504, detail=f"Таймаут при анализе изображения. Файл может быть слишком большим или поврежденным.")
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")
    
    finally:
        # Удаление временного файла
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)


@router.post("/analyze/video", response_model=AnalysisResponse)
async def analyze_video(file: UploadFile = File(...)):
    """
    Анализ метаданных видео
    
    Поддерживаемые форматы: MP4, MOV, MKV
    """
    # Создание временного файла
    temp_file = None
    try:
        content = await file.read()
        
        # Валидация размера файла
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Файл слишком большой (максимум 100MB)")
        
        # Валидация MIME типа
        allowed_types = ["video/mp4", "video/quicktime", "video/x-matroska"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Неподдерживаемый тип файла. Разрешены: MP4, MOV, MKV"
            )
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            tmp.write(content)
            temp_file = tmp.name
        
        # Анализ видео
        analyzer = VideoAnalyzer()
        metadata = analyzer.analyze(temp_file)
        
        # Детекция ИИ
        ai_detector = AIDetector()
        ai_indicators = ai_detector.detect_ai_signs(metadata, file_type="video")
        
        # Генерация отчета
        report_gen = ReportGenerator()
        report_data = report_gen.format_analysis_result(
            file_type="video",
            metadata=metadata,
            ai_indicators=ai_indicators
        )
        
        # Добавляем информацию о файле
        file_size_mb = len(content) / (1024 * 1024)
        report_data["file_info"] = {
            "name": file.filename or "Неизвестно",
            "size": len(content),
            "size_formatted": f"{file_size_mb:.2f} MB" if file_size_mb >= 1 else f"{len(content) / 1024:.2f} KB"
        }
        
        # Генерация PDF отчета
        report_path = report_gen.generate_pdf_report(report_data, temp_file)
        
        return AnalysisResponse(
            file_type="video",
            summary=report_data["summary"],
            metadata=report_data["metadata"],
            ai_indicators={
                "software_detected": ai_indicators.get("software_detected", []),
                "heuristics": ai_indicators.get("heuristics", {}),
                "anomalies": ai_indicators.get("anomalies", []),
                "evidence_from_metadata": ai_indicators.get("evidence_from_metadata") or [],
            },
            report_url=f"/api/reports/{os.path.basename(report_path)}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")
    
    finally:
        # Удаление временного файла
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)


@router.post("/analyze/document", response_model=AnalysisResponse)
async def analyze_document(file: UploadFile = File(...)):
    """
    Анализ документа Word (.docx): извлечение всех изображений и проверка каждого на признаки ИИ.
    """
    temp_file = None
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Файл слишком большой (максимум 100MB)")

        fn = (file.filename or "").lower()
        if not fn.endswith(".docx"):
            raise HTTPException(
                status_code=400,
                detail="Поддерживается только формат Word (.docx)",
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(content)
            temp_file = tmp.name

        doc_analyzer = DocumentAnalyzer()
        doc_result = doc_analyzer.analyze_document(temp_file)

        images_count = doc_result["images_count"]
        if images_count == 0:
            summary = Summary(
                location=None,
                date_time=None,
                source="Word документ (изображений не найдено)",
                ai_probability=0,
                confidence="low",
            )
            report_data = {
                "file_type": "document",
                "summary": {
                    "location": None,
                    "date_time": None,
                    "source": "Word документ (изображений не найдено)",
                    "ai_probability": 0,
                    "confidence": "low",
                },
                "metadata": {"images": [], "images_count": 0, "images_with_ai_count": 0},
                "ai_indicators": {
                    "software_detected": [],
                    "heuristics": {},
                    "anomalies": [],
                    "evidence_from_metadata": [],
                },
                "file_info": {
                    "name": file.filename or "document.docx",
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
                source=f"Word документ: изображений {images_count}, с признаками ИИ — {doc_result['images_with_ai_count']}",
                ai_probability=agg["ai_probability"],
                confidence=agg["confidence"],
            )
            report_gen = ReportGenerator()
            report_data = {
                "file_type": "document",
                "summary": {
                    "location": None,
                    "date_time": None,
                    "source": f"Word документ: изображений {images_count}, с признаками ИИ — {doc_result['images_with_ai_count']}",
                    "ai_probability": agg["ai_probability"],
                    "confidence": agg["confidence"],
                },
                "metadata": {
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
                    "name": file.filename or "document.docx",
                    "size": len(content),
                    "size_formatted": f"{len(content) / (1024*1024):.2f} MB" if len(content) >= 1024 * 1024 else f"{len(content) / 1024:.2f} KB",
                },
            }
            report_data["generated_at"] = __import__("datetime").datetime.now().isoformat()
            report_gen = ReportGenerator()
            report_path = report_gen.generate_pdf_report(report_data, temp_file)

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
            report_url=f"/api/reports/{os.path.basename(report_path)}",
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
    reports_dir = os.path.join(tempfile.gettempdir(), "deepfake_reports")
    report_path = os.path.join(reports_dir, report_filename)
    
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Отчет не найден")
    
    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=report_filename
    )

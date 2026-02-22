"""
Анализатор документов Word (.docx): извлечение изображений и проверка на признаки ИИ.
DOCX — это ZIP-архив, изображения лежат в word/media/.
"""
import zipfile
import os
import tempfile
import logging
from typing import Dict, Any, List, Tuple

from app.services.image_analyzer import ImageAnalyzer
from app.services.ai_detector import AIDetector

logger = logging.getLogger(__name__)

# Расширения изображений, которые могут быть в Word
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".emf", ".wmf"}


class DocumentAnalyzer:
    """Извлечение изображений из .docx и анализ каждого на признаки ИИ."""

    def __init__(self):
        self.image_analyzer = ImageAnalyzer()
        self.ai_detector = AIDetector()

    def extract_images(self, docx_path: str) -> List[Tuple[str, str]]:
        """
        Извлекает все изображения из .docx во временные файлы.
        
        Returns:
            Список пар (имя_файла_в_документе, путь_к_временному_файлу)
        """
        extracted = []
        temp_dir = tempfile.mkdtemp(prefix="docx_images_")
        
        try:
            with zipfile.ZipFile(docx_path, "r") as zf:
                for name in zf.namelist():
                    # Нормализуем путь (ZIP может содержать \ на Windows)
                    name_norm = name.replace("\\", "/").lower()
                    if not name_norm.startswith("word/media/"):
                        continue
                    base = os.path.basename(name)
                    ext = os.path.splitext(base)[1].lower()
                    if ext not in IMAGE_EXTENSIONS:
                        continue
                    data = zf.read(name)
                    out_path = os.path.join(temp_dir, base)
                    with open(out_path, "wb") as f:
                        f.write(data)
                    extracted.append((base, out_path))
        except zipfile.BadZipFile:
            logger.error("Файл не является корректным DOCX (ZIP)")
            raise ValueError("Файл не является корректным документом Word (.docx)")
        except Exception as e:
            logger.exception("Ошибка при извлечении изображений из DOCX")
            raise ValueError(f"Не удалось прочитать документ: {e!s}")

        return extracted

    def analyze_document(self, docx_path: str) -> Dict[str, Any]:
        """
        Анализирует документ: извлекает изображения, для каждого запускает
        анализ метаданных и детекцию ИИ, возвращает сводный результат.
        """
        image_paths = self.extract_images(docx_path)
        
        if not image_paths:
            return {
                "images_count": 0,
                "images_with_ai_count": 0,
                "max_ai_probability": 0,
                "images": [],
                "aggregated": {
                    "software_detected": [],
                    "anomalies": [],
                    "evidence_from_metadata": [],
                    "ai_probability": 0,
                    "confidence": "low",
                },
            }

        images_results = []
        all_software = set()
        all_anomalies = []
        all_evidence = []
        max_ai_prob = 0
        images_with_ai = 0

        for filename, img_path in image_paths:
            try:
                metadata = self.image_analyzer.analyze(img_path)
                ai_indicators = self.ai_detector.detect_ai_signs(metadata, file_type="image")
            except Exception as e:
                logger.warning("Ошибка анализа изображения %s: %s", filename, e)
                metadata = {"error": str(e)}
                ai_indicators = {
                    "software_detected": [],
                    "anomalies": [],
                    "evidence_from_metadata": [],
                    "ai_probability": 0,
                    "confidence": "low",
                }

            prob = ai_indicators.get("ai_probability", 0)
            if prob > 0:
                images_with_ai += 1
            max_ai_prob = max(max_ai_prob, prob)
            all_software.update(ai_indicators.get("software_detected", []))
            all_anomalies.extend(ai_indicators.get("anomalies", []))
            ev = ai_indicators.get("evidence_from_metadata") or []
            all_evidence.extend(ev)

            images_results.append({
                "filename": filename,
                "metadata": metadata,
                "ai_indicators": {
                    "software_detected": ai_indicators.get("software_detected", []),
                    "heuristics": ai_indicators.get("heuristics", {}),
                    "anomalies": ai_indicators.get("anomalies", []),
                    "evidence_from_metadata": ev,
                    "ai_probability": prob,
                    "confidence": ai_indicators.get("confidence", "low"),
                },
            })

        # Удаляем временную папку с извлечёнными изображениями
        temp_dir = os.path.dirname(image_paths[0][1])
        try:
            for _, p in image_paths:
                if os.path.exists(p):
                    os.unlink(p)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except OSError:
            pass

        return {
            "images_count": len(images_results),
            "images_with_ai_count": images_with_ai,
            "max_ai_probability": max_ai_prob,
            "images": images_results,
            "aggregated": {
                "software_detected": list(all_software),
                "anomalies": all_anomalies,
                "evidence_from_metadata": all_evidence,
                "ai_probability": max_ai_prob,
                "confidence": "high" if images_with_ai > 0 else "low",
            },
        }

"""
Анализатор офисных документов (.docx/.pptx):
- извлечение свойств документа из docProps/*.xml
- извлечение встроенных изображений
- анализ каждого изображения на признаки ИИ
"""
import zipfile
import os
import tempfile
import logging
import shutil
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

from app.services.image_analyzer import ImageAnalyzer
from app.services.ai_detector import AIDetector

logger = logging.getLogger(__name__)

# Расширения изображений, которые могут быть в Word
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".emf", ".wmf"}


class DocumentAnalyzer:
    """Извлечение метаданных и изображений из .docx/.pptx."""

    DOCX_MEDIA_PREFIX = "word/media/"
    PPTX_MEDIA_PREFIX = "ppt/media/"

    def __init__(self):
        self.image_analyzer = ImageAnalyzer()
        self.ai_detector = AIDetector()

    def _detect_document_type(self, archive_names: List[str]) -> str:
        names_norm = [name.replace("\\", "/").lower() for name in archive_names]
        has_word = any(name.startswith("word/") for name in names_norm)
        has_ppt = any(name.startswith("ppt/") for name in names_norm)

        if has_word and not has_ppt:
            return "word"
        if has_ppt and not has_word:
            return "powerpoint"
        if has_word and has_ppt:
            # Редкий случай гибридного содержимого; выбираем по приоритету Word.
            return "word"
        raise ValueError("Не удалось определить тип офисного документа (ожидался DOCX/PPTX)")

    def _parse_xml_from_zip(self, zf: zipfile.ZipFile, member: str) -> Optional[ET.Element]:
        try:
            raw = zf.read(member)
        except KeyError:
            return None

        try:
            return ET.fromstring(raw)
        except ET.ParseError:
            logger.warning("Не удалось распарсить XML: %s", member)
            return None

    def _extract_document_metadata(self, zf: zipfile.ZipFile, document_type: str) -> Dict[str, Any]:
        ns = {
            "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/",
            "ep": "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
        }

        core_root = self._parse_xml_from_zip(zf, "docProps/core.xml")
        app_root = self._parse_xml_from_zip(zf, "docProps/app.xml")

        metadata = {
            "document_type": document_type,
            "creator": None,
            "last_modified_by": None,
            "created": None,
            "modified": None,
            "last_printed": None,
            "revision": None,
            "application": None,
            "app_version": None,
            "pages": None,
            "slides": None,
            "words": None,
            "characters": None,
            "characters_with_spaces": None,
            "total_edit_time": None,
            "template": None,
            "company": None,
        }

        if core_root is not None:
            metadata["creator"] = core_root.findtext("dc:creator", default=None, namespaces=ns)
            metadata["last_modified_by"] = core_root.findtext("cp:lastModifiedBy", default=None, namespaces=ns)
            metadata["created"] = core_root.findtext("dcterms:created", default=None, namespaces=ns)
            metadata["modified"] = core_root.findtext("dcterms:modified", default=None, namespaces=ns)
            metadata["last_printed"] = core_root.findtext("cp:lastPrinted", default=None, namespaces=ns)
            metadata["revision"] = core_root.findtext("cp:revision", default=None, namespaces=ns)

        if app_root is not None:
            metadata["application"] = app_root.findtext("ep:Application", default=None, namespaces=ns)
            metadata["app_version"] = app_root.findtext("ep:AppVersion", default=None, namespaces=ns)
            metadata["pages"] = app_root.findtext("ep:Pages", default=None, namespaces=ns)
            metadata["slides"] = app_root.findtext("ep:Slides", default=None, namespaces=ns)
            metadata["words"] = app_root.findtext("ep:Words", default=None, namespaces=ns)
            metadata["characters"] = app_root.findtext("ep:Characters", default=None, namespaces=ns)
            metadata["characters_with_spaces"] = app_root.findtext("ep:CharactersWithSpaces", default=None, namespaces=ns)
            metadata["total_edit_time"] = app_root.findtext("ep:TotalTime", default=None, namespaces=ns)
            metadata["template"] = app_root.findtext("ep:Template", default=None, namespaces=ns)
            metadata["company"] = app_root.findtext("ep:Company", default=None, namespaces=ns)

        return metadata

    def _extract_images(self, office_path: str, media_prefix: str) -> List[Dict[str, Any]]:
        """
        Извлекает все изображения из офисного ZIP-документа во временные файлы.

        Returns:
            Список объектов:
            - filename: имя файла
            - archive_path: путь внутри архива
            - temp_path: путь к временному файлу
            - size: размер извлеченного файла
            - extension: расширение
        """
        extracted: List[Dict[str, Any]] = []
        temp_dir = tempfile.mkdtemp(prefix="office_images_")

        try:
            with zipfile.ZipFile(office_path, "r") as zf:
                for name in zf.namelist():
                    name_norm = name.replace("\\", "/").lower()
                    if not name_norm.startswith(media_prefix):
                        continue

                    base = os.path.basename(name)
                    ext = os.path.splitext(base)[1].lower()
                    if ext not in IMAGE_EXTENSIONS:
                        continue

                    data = zf.read(name)
                    safe_rel = name_norm.replace("/", "__")
                    out_path = os.path.join(temp_dir, safe_rel)
                    with open(out_path, "wb") as f:
                        f.write(data)

                    extracted.append(
                        {
                            "filename": base,
                            "archive_path": name.replace("\\", "/"),
                            "temp_path": out_path,
                            "size": len(data),
                            "extension": ext,
                        }
                    )
        except zipfile.BadZipFile:
            logger.error("Файл не является корректным офисным ZIP-документом")
            raise ValueError("Файл не является корректным документом DOCX/PPTX")
        except Exception as e:
            logger.exception("Ошибка при извлечении изображений из офисного документа")
            raise ValueError(f"Не удалось прочитать документ: {e!s}")

        if not extracted:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return extracted

    def analyze_document(self, office_path: str) -> Dict[str, Any]:
        """
        Анализирует DOCX/PPTX: метаданные документа + анализ встроенных изображений.
        """
        try:
            with zipfile.ZipFile(office_path, "r") as zf:
                archive_names = zf.namelist()
                document_type = self._detect_document_type(archive_names)
                document_metadata = self._extract_document_metadata(zf, document_type)
        except zipfile.BadZipFile:
            raise ValueError("Файл не является корректным документом DOCX/PPTX")

        media_prefix = self.DOCX_MEDIA_PREFIX if document_type == "word" else self.PPTX_MEDIA_PREFIX
        extracted_images = self._extract_images(office_path, media_prefix=media_prefix)

        images_results: List[Dict[str, Any]] = []
        all_software = set()
        all_anomalies = []
        all_evidence = []
        max_ai_prob = 0
        images_with_ai = 0

        for image_entry in extracted_images:
            filename = image_entry["filename"]
            img_path = image_entry["temp_path"]

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

            images_results.append(
                {
                    "filename": filename,
                    "archive_path": image_entry.get("archive_path"),
                    "size": image_entry.get("size"),
                    "extension": image_entry.get("extension"),
                    "metadata": metadata,
                    "ai_indicators": {
                        "software_detected": ai_indicators.get("software_detected", []),
                        "heuristics": ai_indicators.get("heuristics", {}),
                        "anomalies": ai_indicators.get("anomalies", []),
                        "evidence_from_metadata": ev,
                        "ai_probability": prob,
                        "confidence": ai_indicators.get("confidence", "low"),
                    },
                }
            )

        if extracted_images:
            temp_dir = os.path.dirname(extracted_images[0]["temp_path"])
            shutil.rmtree(temp_dir, ignore_errors=True)

        return {
            "document_type": document_type,
            "document_metadata": document_metadata,
            "embedded_images": [
                {
                    "filename": image["filename"],
                    "archive_path": image.get("archive_path"),
                    "size": image.get("size"),
                    "extension": image.get("extension"),
                }
                for image in images_results
            ],
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

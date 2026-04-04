# docx/pptx: docprops, картинки из media/, прогон через imageanalyzer+ai
import zipfile
import os
import logging
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional

from app.services.image_analyzer import ImageAnalyzer
from app.services.ai_detector import AIDetector
from app.services.score_fusion import fuse_image_scores
from app import ml_bridge

logger = logging.getLogger(__name__)

# несколько вложений — в потоках, exiftool в сабпроцессе и так отпускает gil
_DOC_IMAGE_MAX_WORKERS = 8


def _attach_programmatic_generation_trace(document_metadata: Dict[str, Any]) -> None:
    # по creator/description и т.д. — намек на автоген (python-docx, pandoc…); наружу только есть/нет
    creator = (document_metadata.get("creator") or "").strip()
    last_mod = (document_metadata.get("last_modified_by") or "").strip()
    description = (document_metadata.get("description") or "").strip()
    application = (document_metadata.get("application") or "").strip()
    company = (document_metadata.get("company") or "").strip()
    template = (document_metadata.get("template") or "").strip()

    cl, dl = creator.lower(), description.lower()
    ll, al = last_mod.lower(), application.lower()
    cyl, tl = company.lower(), template.lower()
    blob = " ".join(x for x in (cl, ll, dl, al, cyl, tl) if x)

    present = (
        "python-docx" in blob
        or "pandoc" in blob
        or "apache poi" in blob
        or "docx4j" in blob
        or "aspose" in blob
    )

    document_metadata["generation_trace_present"] = present
    document_metadata["generation_trace_label"] = "Есть" if present else "Нет"
    document_metadata["generation_trace_hints"] = []

# Расширения изображений, которые могут быть в Word
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".emf", ".wmf"}

def _analyze_single_embedded_image(
    image_analyzer: ImageAnalyzer,
    ai_detector: AIDetector,
    image_entry: Dict[str, Any],
) -> Dict[str, Any]:
    # одна картинка из архива: мета + эвристика + ml (для thread pool)
    filename = image_entry["filename"]
    blob = image_entry["data"]

    try:
        metadata = image_analyzer.analyze(
            file_bytes=blob,
            stdin_label=image_entry.get("archive_path") or filename,
        )
        if isinstance(metadata, dict) and "error" not in metadata:
            DocumentAnalyzer._annotate_embedded_image_metadata(
                metadata,
                archive_path=image_entry["archive_path"],
                logical_filename=filename,
                zip_entry_modified=image_entry.get("zip_entry_modified"),
            )
        ai_indicators = ai_detector.detect_ai_signs(metadata, file_type="image")
        metadata_score = int(ai_indicators.get("metadata_score", ai_indicators.get("ai_probability", 0)))
        ml_metadata_score, ml_ok = ml_bridge.predict_metadata_ml_safe(metadata)
        final_score, fusion_method = fuse_image_scores(
            metadata_score,
            ml_metadata_score,
            ai_indicators,
            ml_ok,
        )
        ai_indicators["metadata_score"] = metadata_score
        ai_indicators["ml_metadata_score"] = ml_metadata_score if ml_ok else None
        ai_indicators["metadata_ml_available"] = ml_ok
        ai_indicators["final_score"] = final_score
        ai_indicators["fusion_method"] = fusion_method
        ai_indicators["ai_probability"] = final_score
        if ml_ok and ml_metadata_score is not None:
            if final_score >= 70 or metadata_score >= 70:
                ai_indicators["confidence"] = "high"
            elif final_score >= 35 or metadata_score >= 35:
                ai_indicators["confidence"] = "medium"
            else:
                ai_indicators["confidence"] = "low"
    except Exception as e:
        logger.warning("Ошибка анализа изображения %s: %s", filename, e)
        metadata = {"error": str(e)}
        ai_indicators = {
            "software_detected": [],
            "anomalies": [],
            "evidence_from_metadata": [],
            "ai_probability": 0,
            "metadata_score": 0,
            "ml_metadata_score": None,
            "metadata_ml_available": False,
            "final_score": 0,
            "fusion_method": "error",
            "confidence": "low",
        }

    prob = ai_indicators.get("ai_probability", 0)
    ms = int(ai_indicators.get("metadata_score", prob))
    meta_for_row = int(ai_indicators.get("metadata_score", ms))
    ev = ai_indicators.get("evidence_from_metadata") or []

    return {
        "filename": filename,
        "archive_path": image_entry.get("archive_path"),
        "zip_entry_modified": image_entry.get("zip_entry_modified"),
        "size": image_entry.get("size"),
        "extension": image_entry.get("extension"),
        "metadata": metadata,
        "ai_indicators": {
            "software_detected": ai_indicators.get("software_detected", []),
            "heuristics": ai_indicators.get("heuristics", {}),
            "anomalies": ai_indicators.get("anomalies", []),
            "evidence_from_metadata": ev,
            "ai_probability": prob,
            "metadata_score": meta_for_row,
            "ml_metadata_score": ai_indicators.get("ml_metadata_score"),
            "final_score": ai_indicators.get("final_score", prob),
            "fusion_method": ai_indicators.get("fusion_method", "metadata_only"),
            "metadata_ml_available": ai_indicators.get("metadata_ml_available", False),
            "confidence": ai_indicators.get("confidence", "low"),
        },
    }


def _format_zipentry_datetime(zinfo: zipfile.ZipInfo) -> Optional[str]:
    # дата записи в zip как в архиве, без tz
    try:
        t = zinfo.date_time
        if not t or len(t) < 6:
            return None
        y, m, d, hh, mm, ss = t[:6]
        if (y, m, d) == (1980, 1, 1) and (hh, mm, ss) == (0, 0, 0):
            return None
        return f"{y:04d}:{m:02d}:{d:02d} {hh:02d}:{mm:02d}:{ss:02d}"
    except Exception:
        return None


class DocumentAnalyzer:
    # разбор офисного zip + картинки

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
            # бывает каша в zip — по умолчанию word
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
            "description": None,
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
            metadata["description"] = core_root.findtext("dc:description", default=None, namespaces=ns)
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

        _attach_programmatic_generation_trace(metadata)
        return metadata

    def _extract_images(self, office_path: str, media_prefix: str) -> List[Dict[str, Any]]:
        # картинки только в ram — иначе exif подхватит даты с диска
        extracted: List[Dict[str, Any]] = []

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

                    zinfo = zf.getinfo(name)
                    data = zf.read(name)

                    extracted.append(
                        {
                            "filename": base,
                            "archive_path": name.replace("\\", "/"),
                            "data": data,
                            "zip_entry_modified": _format_zipentry_datetime(zinfo),
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

        return extracted

    @staticmethod
    def _annotate_embedded_image_metadata(
        metadata: Dict[str, Any],
        *,
        archive_path: str,
        logical_filename: str,
        zip_entry_modified: Optional[str],
    ) -> None:
        # если в file.directory был temp — подменим на путь внутри дока; плюс блок office archive; exiftool как есть
        exif = metadata.get("exif")
        if not isinstance(exif, dict):
            return
        gm = exif.get("_grouped_metadata")
        if not isinstance(gm, dict):
            return

        file_rows = gm.get("File")
        if isinstance(file_rows, list) and file_rows:
            new_rows: List[List[str]] = []
            for row in file_rows:
                if not row or len(row) < 2:
                    continue
                key_raw, val = str(row[0]), str(row[1])
                key_n = key_raw.replace(" ", "").lower()
                if key_n == "directory" and (
                    "temp" in val.lower()
                    or "tmp" in val.lower()
                    or "appdata" in val.lower()
                ):
                    new_rows.append(["Directory", f"(в документе) {archive_path}"])
                    continue
                new_rows.append([key_raw, val])
            gm["File"] = new_rows

        office_rows: List[List[str]] = [
            ["Path in document", archive_path],
            ["File name", logical_filename],
        ]
        if zip_entry_modified:
            office_rows.insert(0, ["ZIP entry modified", zip_entry_modified])
        gm["Office archive (ZIP)"] = office_rows

    def analyze_document(self, office_path: str) -> Dict[str, Any]:
        # весь док: свойства + все вложенные картинки
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
        max_metadata_score = 0
        max_ml_metadata_score = 0
        any_metadata_ml = False
        images_with_ai = 0

        if len(extracted_images) <= 1:
            for image_entry in extracted_images:
                images_results.append(
                    _analyze_single_embedded_image(
                        self.image_analyzer,
                        self.ai_detector,
                        image_entry,
                    )
                )
        else:
            workers = min(_DOC_IMAGE_MAX_WORKERS, len(extracted_images))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [
                    pool.submit(
                        _analyze_single_embedded_image,
                        self.image_analyzer,
                        self.ai_detector,
                        ie,
                    )
                    for ie in extracted_images
                ]
                images_results = [f.result() for f in futures]

        for row in images_results:
            ai_indicators = row.get("ai_indicators") or {}
            prob = ai_indicators.get("ai_probability", 0)
            ms = int(ai_indicators.get("metadata_score", prob))
            mls = ai_indicators.get("ml_metadata_score")
            if prob > 0:
                images_with_ai += 1
            max_ai_prob = max(max_ai_prob, prob)
            max_metadata_score = max(max_metadata_score, ms)
            if mls is not None:
                max_ml_metadata_score = max(max_ml_metadata_score, int(mls))
            if ai_indicators.get("metadata_ml_available"):
                any_metadata_ml = True
            all_software.update(ai_indicators.get("software_detected", []))
            all_anomalies.extend(ai_indicators.get("anomalies", []))
            all_evidence.extend(ai_indicators.get("evidence_from_metadata") or [])

        plain_text = ""
        doc_nlp_ml_score = None
        doc_nlp_ml_available = False
        if document_type == "word":
            try:
                plain_text = ml_bridge.extract_docx_plain_text_safe(office_path)
                doc_nlp_ml_score, doc_nlp_ml_available = ml_bridge.predict_docx_nlp_safe(
                    plain_text or None
                )
            except Exception:
                pass

        return {
            "document_type": document_type,
            "document_metadata": document_metadata,
            "document_plain_text_chars": len(plain_text),
            "doc_nlp_ml_score": doc_nlp_ml_score,
            "doc_nlp_ml_available": doc_nlp_ml_available,
            "embedded_images": [
                {
                    "filename": image["filename"],
                    "archive_path": image.get("archive_path"),
                    "zip_entry_modified": image.get("zip_entry_modified"),
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
                "metadata_score": max_metadata_score,
                "ml_metadata_score": max_ml_metadata_score if any_metadata_ml else None,
                "final_score": max_ai_prob,
                "metadata_ml_available": any_metadata_ml,
                "fusion_method": "per_image_max",
                "confidence": "high" if images_with_ai > 0 else "low",
            },
        }

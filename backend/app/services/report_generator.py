from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
import os
import tempfile
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

REPORTS_DIR = os.path.join(tempfile.gettempdir(), "deepfake_reports")

_UNICODE_FONT_REG: Optional[str] = None
_UNICODE_FONT_BOLD: Optional[str] = None

# палитра pdf
_COLOR_TEXT = colors.HexColor("#111827")
_COLOR_MUTED = colors.HexColor("#6b7280")
_COLOR_BORDER = colors.HexColor("#e5e7eb")
_COLOR_HEADER_BG = colors.HexColor("#374151")
_COLOR_HEADER_TX = colors.HexColor("#f9fafb")
_COLOR_ROW_ALT = colors.HexColor("#f9fafb")
_COLOR_ROW = colors.white


def _content_width() -> float:
    # ширина колонки на a4, поля по дюйму с каждой стороны
    return A4[0] - 1.5 * inch


def _register_unicode_pdf_fonts() -> Tuple[str, str]:
    # ttf с кириллицей или helvetica
    global _UNICODE_FONT_REG, _UNICODE_FONT_BOLD
    if _UNICODE_FONT_REG is not None:
        return _UNICODE_FONT_REG, _UNICODE_FONT_BOLD or _UNICODE_FONT_REG

    windir = os.environ.get("WINDIR", r"C:\Windows")
    regular_candidates = [
        os.path.join(windir, "Fonts", "arial.ttf"),
        os.path.join(windir, "Fonts", "Arial.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    bold_candidates = [
        os.path.join(windir, "Fonts", "arialbd.ttf"),
        os.path.join(windir, "Fonts", "Arialbd.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ]

    reg_path = next((p for p in regular_candidates if p and os.path.isfile(p)), None)
    bold_path = next((p for p in bold_candidates if p and os.path.isfile(p)), None)

    name = "DeepfakeReportSans"
    name_bold = "DeepfakeReportSans-Bold"

    if reg_path:
        try:
            pdfmetrics.registerFont(TTFont(name, reg_path))
            _UNICODE_FONT_REG = name
            if bold_path:
                pdfmetrics.registerFont(TTFont(name_bold, bold_path))
                _UNICODE_FONT_BOLD = name_bold
            else:
                _UNICODE_FONT_BOLD = name
            pdfmetrics.registerFontFamily(
                name,
                normal=name,
                bold=name_bold if bold_path else name,
                italic=name,
                boldItalic=name_bold if bold_path else name,
            )
            return _UNICODE_FONT_REG, _UNICODE_FONT_BOLD
        except Exception:
            pass

    _UNICODE_FONT_REG = "Helvetica"
    _UNICODE_FONT_BOLD = "Helvetica-Bold"
    return _UNICODE_FONT_REG, _UNICODE_FONT_BOLD


def _hr_line(w: float) -> Table:
    # линия-разделитель
    t = Table([[""]], colWidths=[w], rowHeights=[1])
    t.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, -1), 0.75, _COLOR_BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return t


def _section_banner(title: str, font_bold: str, width: float) -> Table:
    # полоса-заголовок как у таблиц
    p = Paragraph(
        title,
        ParagraphStyle(
            "SectionBanner",
            fontName=font_bold,
            fontSize=11,
            textColor=_COLOR_HEADER_TX,
            leading=14,
            spaceBefore=0,
            spaceAfter=0,
        ),
    )
    t = Table([[p]], colWidths=[width])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _COLOR_HEADER_BG),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


def _kv_table(
    rows: List[List[str]],
    font_reg: str,
    font_bold: str,
    col_label: float = 2.15 * inch,
) -> Table:
    # key-value, первая строка — шапка
    w = _content_width()
    cw = [col_label, w - col_label]
    n = len(rows)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), _COLOR_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), _COLOR_HEADER_TX),
        ("FONTNAME", (0, 0), (-1, 0), font_bold),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 1), (-1, -1), font_reg),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), _COLOR_TEXT),
        ("TOPPADDING", (0, 1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
    ]
    if n > 2:
        style_cmds.append(
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_COLOR_ROW, _COLOR_ROW_ALT])
        )
    tbl = Table(rows, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


class ReportGenerator:
    # pdf и прочее

    def __init__(self):
        self.reports_dir = REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)

    def format_analysis_result(
        self,
        file_type: str,
        metadata: Dict[str, Any],
        ai_indicators: Dict[str, Any],
    ) -> Dict[str, Any]:
        summary = self._generate_summary(file_type, metadata, ai_indicators)
        return {
            "file_type": file_type,
            "summary": summary,
            "metadata": metadata,
            "ai_indicators": ai_indicators,
            "generated_at": datetime.now().isoformat(),
        }

    def _generate_summary(
        self,
        file_type: str,
        metadata: Dict[str, Any],
        ai_indicators: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "location": None,
            "date_time": None,
            "source": metadata.get("document_metadata", {}).get("creator")
            or "Офисный документ",
            "ai_probability": ai_indicators.get("ai_probability", 0),
            "confidence": ai_indicators.get("confidence", "low"),
        }

    def generate_json_report(self, report_data: Dict[str, Any]) -> str:
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.reports_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        return filepath

    def generate_pdf_report(
        self, report_data: Dict[str, Any], original_file: Optional[str] = None
    ) -> str:
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.reports_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
            title="Отчёт об анализе метаданных",
        )
        story: List[Any] = []
        styles = getSampleStyleSheet()
        font_reg, font_bold = _register_unicode_pdf_fonts()
        cw = _content_width()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName=font_bold,
            fontSize=18,
            textColor=_COLOR_TEXT,
            spaceAfter=6,
            alignment=TA_CENTER,
            leading=22,
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName=font_reg,
            fontSize=10,
            textColor=_COLOR_MUTED,
            alignment=TA_CENTER,
            spaceAfter=16,
            leading=14,
        )
        body = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName=font_reg,
            fontSize=10,
            textColor=_COLOR_TEXT,
            spaceAfter=6,
            leading=14,
            alignment=TA_LEFT,
        )
        body_small = ParagraphStyle(
            "BodySmall",
            parent=body,
            fontSize=9,
            textColor=_COLOR_MUTED,
            spaceAfter=4,
        )
        img_card_title_style = ParagraphStyle(
            "ImageCardTitle",
            parent=styles["Normal"],
            fontName=font_bold,
            fontSize=11,
            textColor=_COLOR_TEXT,
            spaceBefore=14,
            spaceAfter=8,
            leading=14,
        )
        bullet = ParagraphStyle(
            "Bullet",
            parent=body,
            leftIndent=14,
            bulletIndent=6,
            spaceAfter=4,
        )

        # Титул
        story.append(Paragraph("Отчёт об анализе метаданных", title_style))
        story.append(
            Paragraph(
                "Документы Microsoft Word и PowerPoint (DOCX, PPTX)",
                subtitle_style,
            )
        )
        story.append(_hr_line(cw))
        story.append(Spacer(1, 0.18 * inch))

        ai_indicators = report_data.get("ai_indicators", {})
        summary = report_data.get("summary", {}) or {}
        ai_prob = ai_indicators.get("ai_probability")
        if ai_prob is None:
            ai_prob = (
                ai_indicators.get("final_score")
                if ai_indicators.get("final_score") is not None
                else summary.get("final_score")
                if summary.get("final_score") is not None
                else summary.get("ai_probability")
            )
        if ai_prob is None:
            ai_prob = 0
        try:
            ai_prob = int(round(float(ai_prob)))
        except (TypeError, ValueError):
            ai_prob = 0
        ai_prob = max(0, min(100, ai_prob))

        if ai_prob < 30:
            ai_color = colors.HexColor("#15803d")
            ai_status = "низкая"
        elif ai_prob < 70:
            ai_color = colors.HexColor("#b45309")
            ai_status = "средняя"
        else:
            ai_color = colors.HexColor("#b91c1c")
            ai_status = "высокая"

        ms = ai_indicators.get("metadata_score")
        mls = ai_indicators.get("ml_metadata_score")
        fs = ai_indicators.get("final_score")
        mma = ai_indicators.get("metadata_ml_available")
        mdinfo = report_data.get("metadata") or {}
        dn_score = mdinfo.get("doc_nlp_ml_score")
        dn_avail = mdinfo.get("doc_nlp_ml_available")

        # 1. Итог проверки
        story.append(_section_banner("1. Итог проверки", font_bold, cw))
        story.append(Spacer(1, 0.1 * inch))

        score_box = Table(
            [
                [
                    Paragraph(
                        f"<font color='{ai_color.hexval()}'><b>{ai_prob}%</b></font>",
                        ParagraphStyle(
                            "BigScore",
                            fontName=font_bold,
                            fontSize=22,
                            alignment=TA_CENTER,
                            leading=26,
                        ),
                    )
                ],
                [
                    Paragraph(
                        f"Сводная оценка риска ИИ: <b>{ai_status}</b>",
                        ParagraphStyle(
                            "ScoreCap",
                            fontName=font_reg,
                            fontSize=10,
                            alignment=TA_CENTER,
                            textColor=_COLOR_MUTED,
                            leading=13,
                        ),
                    )
                ],
            ],
            colWidths=[cw],
        )
        score_box.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("BOX", (0, 0), (-1, -1), 0.75, _COLOR_BORDER),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
                ]
            )
        )
        story.append(score_box)
        story.append(Spacer(1, 0.12 * inch))

        if ms is not None or mls is not None or fs is not None or mdinfo.get("document_type") == "word":
            h_ml = str(mls) + "%" if mls is not None else "—"
            if not mma and mls is None:
                h_ml = "—"
            detail_rows = [
                ["Показатель", "Значение"],
                [
                    "Эвристика",
                    f"{ms}%" if ms is not None else "—",
                ],
                [
                    "ML (метаданные изображений)",
                    h_ml + (" (модель загружена)" if mma else " (модель не загружена)"),
                ],
            ]
            if mdinfo.get("document_type") == "word":
                if dn_avail and dn_score is not None:
                    nlp_cell = f"{dn_score}% (модель текста загружена)"
                elif not dn_avail:
                    nlp_cell = "-"
                else:
                    nlp_cell = "—"
                detail_rows.append(["ML (текст DOCX)", nlp_cell])
            detail_rows.append(
                [
                    "Итог",
                    f"{fs if fs is not None else ai_prob}%",
                ]
            )
            story.append(
                Paragraph("Разбивка оценок", body_small)
            )
            story.append(Spacer(1, 0.06 * inch))
            story.append(_kv_table(detail_rows, font_reg, font_bold))

        story.append(Spacer(1, 0.2 * inch))

        # 2. Файл
        story.append(_section_banner("2. Загруженный файл", font_bold, cw))
        story.append(Spacer(1, 0.1 * inch))
        file_info = report_data.get("file_info", {})
        file_rows = [
            ["Параметр", "Значение"],
            ["Тип", str(report_data.get("file_type", "—")).upper()],
            ["Имя файла", str(file_info.get("name", "—"))],
            [
                "Размер",
                str(file_info.get("size_formatted", "—"))
                if file_info.get("size")
                else "—",
            ],
            ["Местоположение", summary.get("location") or "—"],
            ["Дата и время", summary.get("date_time") or "—"],
            ["Источник (сводка)", summary.get("source") or "—"],
        ]
        story.append(_kv_table(file_rows, font_reg, font_bold))
        story.append(Spacer(1, 0.16 * inch))

        # 3. Факты из метаданных
        evidence = ai_indicators.get("evidence_from_metadata", [])
        if evidence:
            story.append(_section_banner("3. Факты из метаданных", font_bold, cw))
            story.append(Spacer(1, 0.1 * inch))
            for fact in evidence:
                safe = (
                    str(fact)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                story.append(Paragraph(f"• {safe}", bullet))
            story.append(Spacer(1, 0.12 * inch))
        else:
            story.append(_section_banner("3. Факты из метаданных", font_bold, cw))
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("Записей не найдено.", body_small))
            story.append(Spacer(1, 0.12 * inch))

        # 4. Признаки
        story.append(_section_banner("4. Признаки и замечания", font_bold, cw))
        story.append(Spacer(1, 0.1 * inch))
        software_detected = ai_indicators.get("software_detected", [])
        if software_detected:
            sw = ", ".join(software_detected)
            sw = (
                sw.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            story.append(Paragraph(f"<b>Обнаруженное ПО:</b> {sw}", body))
        else:
            story.append(Paragraph("<b>Обнаруженное ПО:</b> нет", body))

        anomalies = ai_indicators.get("anomalies", [])
        if anomalies:
            story.append(Spacer(1, 0.06 * inch))
            story.append(Paragraph("<b>Аномалии и подозрительные признаки</b>", body))
            for an in anomalies:
                s = (
                    str(an)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                story.append(Paragraph(f"• {s}", bullet))
        else:
            story.append(Paragraph("Аномалии: не обнаружены.", body_small))

        story.append(Spacer(1, 0.2 * inch))
        story.append(PageBreak())

        # 5. Документ и изображения
        story.append(_section_banner("5. Документ и встроенные изображения", font_bold, cw))
        story.append(Spacer(1, 0.1 * inch))
        metadata = report_data.get("metadata", {})
        self._add_document_metadata(
            story,
            metadata,
            body,
            body_small,
            img_card_title_style,
            bullet,
            font_reg,
            font_bold,
        )

        story.append(Spacer(1, 0.35 * inch))
        generated_at = report_data.get("generated_at", "")
        if generated_at:
            try:
                dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%d.%m.%Y %H:%M:%S")
            except Exception:
                formatted_date = generated_at
        else:
            formatted_date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontName=font_reg,
            fontSize=8,
            textColor=_COLOR_MUTED,
            alignment=TA_CENTER,
        )
        story.append(_hr_line(cw))
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(f"Дата формирования отчёта: {formatted_date}", footer_style)
        )

        doc.build(story)
        return filepath

    def _add_document_metadata(
        self,
        story,
        metadata,
        body,
        body_small,
        img_card_title_style,
        bullet,
        font_reg: str,
        font_bold: str,
    ):
        def _escape(s):
            if s is None:
                return ""
            s = str(s)
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        def _format_value(value):
            if value is None or value == "":
                return "—"
            text = str(value)
            return text if len(text) <= 200 else text[:197] + "..."

        document_type = metadata.get("document_type", "word")
        document_label = "PowerPoint" if document_type == "powerpoint" else "Word"
        document_meta = metadata.get("document_metadata", {}) or {}
        images = metadata.get("images", [])
        images_count = metadata.get("images_count", 0)
        images_with_ai = metadata.get("images_with_ai_count", 0)

        story.append(
            Paragraph(
                f"<b>Тип документа:</b> {document_label}",
                body,
            )
        )
        story.append(Spacer(1, 0.1 * inch))

        meta_rows = [["Поле", "Значение"]]
        trace_label = document_meta.get("generation_trace_label")
        if trace_label is None:
            trace_label = "Есть" if document_meta.get("generation_trace_present") else "Нет"
        meta_fields = [
            ("Автор", document_meta.get("creator")),
            ("Последний редактор", document_meta.get("last_modified_by")),
            ("След генерации", trace_label),
            ("Описание (dc:description)", document_meta.get("description")),
            ("Создан", document_meta.get("created")),
            ("Изменён", document_meta.get("modified")),
            ("Печать", document_meta.get("last_printed")),
            ("Ревизия", document_meta.get("revision")),
            ("Приложение", document_meta.get("application")),
            ("Версия приложения", document_meta.get("app_version")),
            ("Страниц", document_meta.get("pages")),
            ("Слайдов", document_meta.get("slides")),
            ("Слов", document_meta.get("words")),
            ("Символов", document_meta.get("characters")),
            ("С пробелами", document_meta.get("characters_with_spaces")),
        ]
        for label, value in meta_fields:
            if value is not None and str(value).strip():
                meta_rows.append([label, _format_value(value)])

        if len(meta_rows) > 1:
            story.append(
                Paragraph("Свойства документа (из файла)", body_small)
            )
            story.append(Spacer(1, 0.06 * inch))
            story.append(_kv_table(meta_rows, font_reg, font_bold))
            story.append(Spacer(1, 0.16 * inch))

        story.append(
            Paragraph(
                f"<b>Встроенные изображения:</b> {images_count} шт.; "
                f"с ненулевой оценкой ИИ — {images_with_ai}.",
                body,
            )
        )
        story.append(Spacer(1, 0.14 * inch))

        if not images:
            story.append(Paragraph("В документе нет извлечённых изображений.", body_small))
            return

        for i, img in enumerate(images):
            fname = _escape(img.get("filename", f"image_{i+1}"))
            source_path = _escape(img.get("archive_path", ""))
            ai_ind = img.get("ai_indicators", {})
            prob = ai_ind.get("ai_probability", 0)
            m_s = ai_ind.get("metadata_score")
            ml_s = ai_ind.get("ml_metadata_score")
            ml_ok = ai_ind.get("metadata_ml_available")

            block: List[Any] = []
            block.append(
                Paragraph(
                    f"<b>Изображение {i + 1}.</b> {_escape(fname)}",
                    img_card_title_style,
                )
            )
            img_rows = [
                ["Параметр", "Значение"],
                ["Итоговая оценка ИИ", f"{prob}%"],
            ]
            if m_s is not None:
                img_rows.append(["Эвристика", f"{m_s}%"])
            if ml_ok and ml_s is not None:
                img_rows.append(["ML", f"{ml_s}%"])
            elif ml_ok is False:
                img_rows.append(["ML", "модель не использована"])
            block.append(_kv_table(img_rows, font_reg, font_bold))

            if source_path:
                block.append(Spacer(1, 0.06 * inch))
                block.append(
                    Paragraph(
                        f"<b>Путь в архиве документа:</b><br/>{source_path}",
                        body_small,
                    )
                )
            sw = ai_ind.get("software_detected") or []
            if sw:
                block.append(
                    Paragraph(
                        "<b>ПО в метаданных:</b> " + _escape(", ".join(sw)),
                        body,
                    )
                )
            anoms = ai_ind.get("anomalies") or []
            if anoms:
                block.append(Paragraph("<b>Замечания</b>", body_small))
                for an in anoms:
                    block.append(Paragraph("• " + _escape(an), bullet))
            block.append(Spacer(1, 0.14 * inch))
            story.append(KeepTogether(block))

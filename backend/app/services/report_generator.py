from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import json
import os
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime

class ReportGenerator:
    """Генератор отчетов в различных форматах"""
    
    def __init__(self):
        self.reports_dir = os.path.join(tempfile.gettempdir(), "deepfake_reports")
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def format_analysis_result(
        self, 
        file_type: str, 
        metadata: Dict[str, Any], 
        ai_indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Форматирование результата анализа для отчета
        
        Returns:
            Словарь с отформатированными данными
        """
        summary = self._generate_summary(file_type, metadata, ai_indicators)
        
        return {
            "file_type": file_type,
            "summary": summary,
            "metadata": metadata,
            "ai_indicators": ai_indicators,
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_summary(
        self, 
        file_type: str, 
        metadata: Dict[str, Any], 
        ai_indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Генерация краткого резюме"""
        summary = {
            "location": None,
            "date_time": None,
            "source": None,
            "ai_probability": ai_indicators.get("ai_probability", 0),
            "confidence": ai_indicators.get("confidence", "low")
        }
        
        if file_type == "image":
            exif = metadata.get("exif", {})
            
            # Местоположение
            if "gps" in exif:
                gps = exif["gps"]
                summary["location"] = f"GPS: {gps.get('latitude', 'N/A')}, {gps.get('longitude', 'N/A')}"
            
            # Дата и время
            if "date_time" in exif:
                summary["date_time"] = str(exif["date_time"])
            
            # Источник (камера)
            camera_parts = []
            if "camera_make" in exif:
                camera_parts.append(exif["camera_make"])
            if "camera_model" in exif:
                camera_parts.append(exif["camera_model"])
            if camera_parts:
                summary["source"] = " ".join(camera_parts)
            elif "software" in exif:
                summary["source"] = exif["software"]
            else:
                summary["source"] = "Неизвестно"
        
        elif file_type == "video":
            container = metadata.get("container", {})
            video_stream = metadata.get("video_stream", {})
            
            # Дата создания
            creation_time = container.get("creation_time") or video_stream.get("creation_time")
            if creation_time:
                summary["date_time"] = creation_time
            
            # Источник (encoder)
            encoder = container.get("encoder") or video_stream.get("encoder")
            if encoder:
                summary["source"] = encoder
            else:
                codec = video_stream.get("codec_name")
                if codec:
                    summary["source"] = f"Кодек: {codec}"
                else:
                    summary["source"] = "Неизвестно"

        return summary
    
    def generate_json_report(self, report_data: Dict[str, Any]) -> str:
        """Генерация JSON отчета"""
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def generate_pdf_report(self, report_data: Dict[str, Any], original_file: Optional[str] = None) -> str:
        """Генерация PDF отчета с визуальными индикаторами"""
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, 
                               leftMargin=0.75*inch, rightMargin=0.75*inch,
                               topMargin=0.75*inch, bottomMargin=0.75*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Стили
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#000000'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#000000'),
            spaceAfter=12,
            spaceBefore=16,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'NormalText',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#000000'),
            spaceAfter=8,
            leading=14
        )
        
        # Заголовок
        story.append(Paragraph("АНАЛИЗ МЕТАДАННЫХ", title_style))
        story.append(Paragraph("Выявление ИИ-модификаций в изображениях и видео", 
                              ParagraphStyle('Subtitle', parent=styles['Normal'], 
                                           fontSize=11, alignment=TA_CENTER, 
                                           textColor=colors.HexColor('#333333'),
                                           spaceAfter=24)))
        story.append(Spacer(1, 0.1*inch))
        
        # Вероятность ИИ-вмешательства
        ai_indicators = report_data.get("ai_indicators", {})
        ai_prob = ai_indicators.get("ai_probability", 0)
        
        if ai_prob < 30:
            ai_color = colors.HexColor('#22c55e')  # green
            ai_status = "Низкая"
        elif ai_prob < 70:
            ai_color = colors.HexColor('#f59e0b')  # orange
            ai_status = "Средняя"
        else:
            ai_color = colors.HexColor('#ef4444')  # red
            ai_status = "Высокая"
        
        prob_style = ParagraphStyle(
            'Probability',
            parent=styles['Normal'],
            fontSize=16,
            textColor=ai_color,
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph(f"<b>Вероятность ИИ-вмешательства: {ai_prob}%</b>", prob_style))
        story.append(Paragraph(f"<b>Уровень:</b> {ai_status}", 
                              ParagraphStyle('Status', parent=normal_style, 
                                           alignment=TA_CENTER, fontSize=11)))
        story.append(Spacer(1, 0.2*inch))
        
        # Информация о файле
        story.append(Paragraph("<b>ИНФОРМАЦИЯ О ФАЙЛЕ</b>", heading_style))
        
        summary = report_data.get("summary", {})
        file_info = report_data.get("file_info", {})
        
        info_data = [
            ["Параметр", "Значение"],
            ["Тип файла", report_data.get("file_type", "N/A").upper()],
            ["Название файла", file_info.get("name", "Не указано")],
            ["Размер файла", file_info.get("size_formatted", "Не указано") if file_info.get("size") else "Не указано"],
            ["Местоположение", summary.get("location") or "Не указано"],
            ["Дата и время", summary.get("date_time") or "Не указано"],
            ["Источник", summary.get("source") or "Неизвестно"],
        ]
        
        info_table = Table(info_data, colWidths=[2.2*inch, 4.3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#000000')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#000000')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # По фактам из метаданных
        evidence = ai_indicators.get("evidence_from_metadata", [])
        if evidence:
            story.append(Paragraph("<b>ПО ФАКТАМ ИЗ МЕТАДАННЫХ</b>", heading_style))
            for fact in evidence:
                story.append(Paragraph(f"• {fact}", normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Обнаруженные признаки ИИ
        story.append(Paragraph("<b>ОБНАРУЖЕННЫЕ ПРИЗНАКИ ИИ</b>", heading_style))
        
        software_detected = ai_indicators.get("software_detected", [])
        if software_detected:
            story.append(Paragraph(f"<b>Обнаруженное ПО:</b> {', '.join(software_detected)}", normal_style))
        else:
            story.append(Paragraph("Обнаруженное ПО: Не обнаружено", normal_style))
        
        anomalies = ai_indicators.get("anomalies", [])
        if anomalies:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("<b>Аномалии и подозрительные признаки:</b>", normal_style))
            for anomaly in anomalies:
                story.append(Paragraph(f"• {anomaly}", normal_style))
        else:
            story.append(Paragraph("Аномалии: Не обнаружено", normal_style))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Детальные метаданные
        story.append(PageBreak())
        story.append(Paragraph("<b>ДЕТАЛЬНЫЕ МЕТАДАННЫЕ</b>", heading_style))
        
        metadata = report_data.get("metadata", {})
        if report_data.get("file_type") == "image":
            self._add_image_metadata(story, metadata, styles, normal_style, heading_style)
        elif report_data.get("file_type") == "document":
            self._add_document_metadata(story, metadata, styles, normal_style, heading_style)
        else:
            self._add_video_metadata(story, metadata, styles, normal_style, heading_style)
        
        # Футер
        story.append(Spacer(1, 0.3*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER
        )
        generated_at = report_data.get('generated_at', '')
        if generated_at:
            try:
                dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%d.%m.%Y %H:%M:%S')
            except:
                formatted_date = generated_at
        else:
            formatted_date = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        
        story.append(Paragraph(
            f"Отчет сгенерирован: {formatted_date}",
            footer_style
        ))
        
        doc.build(story)
        return filepath
    
    def _add_image_metadata(self, story, metadata, styles, normal_style, heading_style):
        """Добавление метаданных изображения в отчет"""
        exif = metadata.get("exif", {})
        xmp = metadata.get("xmp", {})
        
        # Фильтруем служебные поля
        skip_keys = {"error", "_c2pa_metadata", "_c2pa_manifest_types", "_c2pa_key_fields", "_c2pa_key_aliases"}
        
        if exif:
            # Фильтруем только значимые поля
            exif_filtered = {k: v for k, v in exif.items() 
                           if k not in skip_keys and v is not None and str(v).strip()}
            
            if exif_filtered:
                story.append(Paragraph("<b>EXIF данные</b>", heading_style))
                exif_data = [["Параметр", "Значение"]]
                for key, value in sorted(exif_filtered.items()):
                    value_str = str(value)
                    # Ограничиваем длину для очень длинных значений
                    if len(value_str) > 150:
                        value_str = value_str[:147] + "..."
                    exif_data.append([key, value_str])
                
                exif_table = Table(exif_data, colWidths=[2.2*inch, 4.3*inch])
                exif_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 1), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                ]))
                story.append(exif_table)
                story.append(Spacer(1, 0.25*inch))
        
        if xmp:
            xmp_filtered = {k: v for k, v in xmp.items() 
                          if k not in skip_keys and v is not None and str(v).strip()}
            
            if xmp_filtered:
                story.append(Paragraph("<b>XMP данные</b>", heading_style))
                xmp_data = [["Параметр", "Значение"]]
                for key, value in sorted(xmp_filtered.items()):
                    value_str = str(value)
                    if len(value_str) > 150:
                        value_str = value_str[:147] + "..."
                    xmp_data.append([key, value_str])
                
                xmp_table = Table(xmp_data, colWidths=[2.2*inch, 4.3*inch])
                xmp_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 1), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                ]))
                story.append(xmp_table)

    def _add_video_metadata(self, story, metadata, styles, normal_style, heading_style):
        """Добавление метаданных видео в отчет"""
        container = metadata.get("container", {})
        video_stream = metadata.get("video_stream", {})
        audio_stream = metadata.get("audio_stream", {})
        
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ])
        
        if container:
            container_filtered = {k: v for k, v in container.items() 
                                if v is not None and str(v).strip()}
            if container_filtered:
                story.append(Paragraph("<b>Метаданные контейнера</b>", heading_style))
                container_data = [["Параметр", "Значение"]]
                for key, value in sorted(container_filtered.items()):
                    value_str = str(value)
                    if len(value_str) > 150:
                        value_str = value_str[:147] + "..."
                    container_data.append([key, value_str])
                
                container_table = Table(container_data, colWidths=[2.2*inch, 4.3*inch])
                container_table.setStyle(table_style)
                story.append(container_table)
                story.append(Spacer(1, 0.25*inch))
        
        if video_stream:
            video_filtered = {k: v for k, v in video_stream.items() 
                            if v is not None and str(v).strip()}
            if video_filtered:
                story.append(Paragraph("<b>Видео поток</b>", heading_style))
                video_data = [["Параметр", "Значение"]]
                for key, value in sorted(video_filtered.items()):
                    value_str = str(value)
                    if len(value_str) > 150:
                        value_str = value_str[:147] + "..."
                    video_data.append([key, value_str])
                
                video_table = Table(video_data, colWidths=[2.2*inch, 4.3*inch])
                video_table.setStyle(table_style)
                story.append(video_table)
                story.append(Spacer(1, 0.25*inch))
        
        if audio_stream:
            audio_filtered = {k: v for k, v in audio_stream.items() 
                           if v is not None and str(v).strip()}
            if audio_filtered:
                story.append(Paragraph("<b>Аудио поток</b>", heading_style))
                audio_data = [["Параметр", "Значение"]]
                for key, value in sorted(audio_filtered.items()):
                    value_str = str(value)
                    if len(value_str) > 150:
                        value_str = value_str[:147] + "..."
                    audio_data.append([key, value_str])
                
                audio_table = Table(audio_data, colWidths=[2.2*inch, 4.3*inch])
                audio_table.setStyle(table_style)
                story.append(audio_table)

    def _add_document_metadata(self, story, metadata, styles, normal_style, heading_style):
        """Добавление в отчёт результатов анализа изображений из Word-документа"""
        def _escape(s):
            if s is None:
                return ""
            s = str(s)
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        images = metadata.get("images", [])
        images_count = metadata.get("images_count", 0)
        images_with_ai = metadata.get("images_with_ai_count", 0)

        story.append(Paragraph(
            f"<b>Документ Word:</b> извлечено изображений — {images_count}, "
            f"с признаками ИИ — {images_with_ai}.",
            normal_style
        ))
        story.append(Spacer(1, 0.2*inch))

        for i, img in enumerate(images):
            fname = _escape(img.get("filename", f"image_{i+1}"))
            ai_ind = img.get("ai_indicators", {})
            prob = ai_ind.get("ai_probability", 0)
            story.append(Paragraph(f"<b>Изображение {i+1}:</b> {fname} — вероятность ИИ {prob}%", heading_style))
            if ai_ind.get("software_detected"):
                story.append(Paragraph(
                    "Обнаруженное ПО: " + _escape(", ".join(ai_ind["software_detected"])),
                    normal_style
                ))
            for anom in ai_ind.get("anomalies", []):
                story.append(Paragraph("• " + _escape(anom), normal_style))
            story.append(Spacer(1, 0.15*inch))

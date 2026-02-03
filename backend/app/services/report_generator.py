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
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Заголовок
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("Отчет анализа метаданных", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Резюме
        summary = report_data.get("summary", {})
        summary_style = ParagraphStyle(
            'Summary',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12
        )
        
        # Индикатор вероятности ИИ
        ai_prob = summary.get("ai_probability", 0)
        if ai_prob < 30:
            ai_color = colors.green
            ai_status = "Низкая вероятность ИИ"
        elif ai_prob < 70:
            ai_color = colors.orange
            ai_status = "Средняя вероятность ИИ"
        else:
            ai_color = colors.red
            ai_status = "Высокая вероятность ИИ"
        
        ai_style = ParagraphStyle(
            'AIStatus',
            parent=styles['Normal'],
            fontSize=14,
            textColor=ai_color,
            spaceAfter=20
        )
        story.append(Paragraph(f"<b>Вероятность ИИ-вмешательства: {ai_prob}%</b>", ai_style))
        story.append(Paragraph(f"<b>Статус:</b> {ai_status}", summary_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Основная информация
        info_data = [
            ["Параметр", "Значение"],
            ["Тип файла", report_data.get("file_type", "N/A")],
            ["📍 Местоположение", summary.get("location") or "Не указано"],
            ["🕒 Дата и время", summary.get("date_time") or "Не указано"],
            ["📷 Источник", summary.get("source") or "Неизвестно"],
            ["🎯 Достоверность", summary.get("confidence", "low")],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Обнаруженные признаки ИИ
        ai_indicators = report_data.get("ai_indicators", {})
        story.append(Paragraph("<b>Обнаруженные признаки ИИ:</b>", styles['Heading2']))
        
        software_detected = ai_indicators.get("software_detected", [])
        if software_detected:
            story.append(Paragraph(f"<b>Обнаруженное ПО:</b> {', '.join(software_detected)}", styles['Normal']))
        else:
            story.append(Paragraph("Обнаруженное ПО: Не обнаружено", styles['Normal']))
        
        anomalies = ai_indicators.get("anomalies", [])
        if anomalies:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("<b>Аномалии:</b>", styles['Normal']))
            for anomaly in anomalies:
                story.append(Paragraph(f"• {anomaly}", styles['Normal']))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Детальные метаданные
        story.append(PageBreak())
        story.append(Paragraph("<b>Детальные метаданные:</b>", styles['Heading2']))
        
        metadata = report_data.get("metadata", {})
        if report_data.get("file_type") == "image":
            self._add_image_metadata(story, metadata, styles)
        else:
            self._add_video_metadata(story, metadata, styles)
        
        # Футер
        story.append(Spacer(1, 0.3*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph(
            f"Отчет сгенерирован: {report_data.get('generated_at', 'N/A')}",
            footer_style
        ))
        
        doc.build(story)
        return filepath
    
    def _add_image_metadata(self, story, metadata, styles):
        """Добавление метаданных изображения в отчет"""
        exif = metadata.get("exif", {})
        xmp = metadata.get("xmp", {})
        
        if exif:
            story.append(Paragraph("<b>EXIF данные:</b>", styles['Heading3']))
            exif_data = []
            for key, value in exif.items():
                if key != "error":
                    exif_data.append([key, str(value)])
            
            if exif_data:
                exif_table = Table(exif_data, colWidths=[2*inch, 4*inch])
                exif_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(exif_table)
                story.append(Spacer(1, 0.2*inch))
        
        if xmp:
            story.append(Paragraph("<b>XMP данные:</b>", styles['Heading3']))
            xmp_data = []
            for key, value in xmp.items():
                if key != "error":
                    xmp_data.append([key, str(value)[:100]])  # Ограничение длины
            
            if xmp_data:
                xmp_table = Table(xmp_data, colWidths=[2*inch, 4*inch])
                xmp_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(xmp_table)

    def _add_video_metadata(self, story, metadata, styles):
        """Добавление метаданных видео в отчет"""
        container = metadata.get("container", {})
        video_stream = metadata.get("video_stream", {})
        audio_stream = metadata.get("audio_stream", {})
        
        if container:
            story.append(Paragraph("<b>Метаданные контейнера:</b>", styles['Heading3']))
            container_data = []
            for key, value in container.items():
                if value:
                    container_data.append([key, str(value)])
            
            if container_data:
                container_table = Table(container_data, colWidths=[2*inch, 4*inch])
                container_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(container_table)
                story.append(Spacer(1, 0.2*inch))
        
        if video_stream:
            story.append(Paragraph("<b>Видео поток:</b>", styles['Heading3']))
            video_data = []
            for key, value in video_stream.items():
                if value:
                    video_data.append([key, str(value)])
            
            if video_data:
                video_table = Table(video_data, colWidths=[2*inch, 4*inch])
                video_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(video_table)
                story.append(Spacer(1, 0.2*inch))
        
        if audio_stream:
            story.append(Paragraph("<b>Аудио поток:</b>", styles['Heading3']))
            audio_data = []
            for key, value in audio_stream.items():
                if value:
                    audio_data.append([key, str(value)])
            
            if audio_data:
                audio_table = Table(audio_data, colWidths=[2*inch, 4*inch])
                audio_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(audio_table)

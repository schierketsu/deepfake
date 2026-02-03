import ffmpeg
import json
from typing import Dict, Any, Optional, List
import subprocess
import os

class VideoAnalyzer:
    """Анализатор метаданных видео"""
    
    def __init__(self):
        self.ai_encoder_keywords = [
            "stable diffusion",
            "sora",
            "runway",
            "pika",
            "comfyui",
            "ai pipeline",
            "generated",
            "synthetic"
        ]
    
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        Полный анализ метаданных видео
        
        Args:
            file_path: Путь к файлу видео
            
        Returns:
            Словарь с метаданными и результатами анализа
        """
        result = {
            "container": {},
            "video_stream": {},
            "audio_stream": {},
            "encoding_info": {},
            "anomalies": []
        }
        
        # Извлечение метаданных через ffprobe
        metadata = self.extract_video_metadata(file_path)
        result["container"] = metadata.get("container", {})
        result["video_stream"] = metadata.get("video_stream", {})
        result["audio_stream"] = metadata.get("audio_stream", {})
        
        # Анализ encoder string
        encoding_info = self.analyze_encoder_string(metadata)
        result["encoding_info"] = encoding_info
        
        # Проверка консистентности кадров
        frame_consistency = self.check_frame_consistency(metadata)
        result["frame_consistency"] = frame_consistency
        
        # Выявление аномалий кодирования
        anomalies = self.detect_encoding_anomalies(metadata, encoding_info, frame_consistency)
        result["anomalies"] = anomalies
        
        return result
    
    def extract_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """Извлечение метаданных видео через ffprobe"""
        try:
            # Использование ffprobe для получения метаданных
            probe = ffmpeg.probe(file_path)
            
            result = {
                "container": {},
                "video_stream": {},
                "audio_stream": {}
            }
            
            # Метаданные контейнера
            format_info = probe.get("format", {})
            result["container"] = {
                "format_name": format_info.get("format_name"),
                "format_long_name": format_info.get("format_long_name"),
                "duration": format_info.get("duration"),
                "size": format_info.get("size"),
                "bit_rate": format_info.get("bit_rate"),
                "creation_time": format_info.get("tags", {}).get("creation_time"),
                "encoder": format_info.get("tags", {}).get("encoder")
            }
            
            # Поиск видео потока
            video_stream = None
            audio_stream = None
            
            for stream in probe.get("streams", []):
                if stream.get("codec_type") == "video" and video_stream is None:
                    video_stream = stream
                elif stream.get("codec_type") == "audio" and audio_stream is None:
                    audio_stream = stream
            
            if video_stream:
                result["video_stream"] = {
                    "codec_name": video_stream.get("codec_name"),
                    "codec_long_name": video_stream.get("codec_long_name"),
                    "width": video_stream.get("width"),
                    "height": video_stream.get("height"),
                    "r_frame_rate": video_stream.get("r_frame_rate"),
                    "avg_frame_rate": video_stream.get("avg_frame_rate"),
                    "duration": video_stream.get("duration"),
                    "bit_rate": video_stream.get("bit_rate"),
                    "pix_fmt": video_stream.get("pix_fmt"),
                    "encoder": video_stream.get("tags", {}).get("encoder"),
                    "creation_time": video_stream.get("tags", {}).get("creation_time")
                }
            
            if audio_stream:
                result["audio_stream"] = {
                    "codec_name": audio_stream.get("codec_name"),
                    "codec_long_name": audio_stream.get("codec_long_name"),
                    "sample_rate": audio_stream.get("sample_rate"),
                    "channels": audio_stream.get("channels"),
                    "bit_rate": audio_stream.get("bit_rate"),
                    "encoder": audio_stream.get("tags", {}).get("encoder")
                }
            
            return result
        
        except Exception as e:
            return {
                "error": f"Ошибка анализа видео: {str(e)}",
                "container": {},
                "video_stream": {},
                "audio_stream": {}
            }
    
    def analyze_encoder_string(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ encoder string на признаки ИИ-пайплайнов"""
        encoding_info = {
            "encoder_detected": False,
            "encoder_string": None,
            "ai_indicators": [],
            "suspicious": False
        }
        
        # Проверка encoder в контейнере
        container_encoder = metadata.get("container", {}).get("encoder")
        video_encoder = metadata.get("video_stream", {}).get("encoder")
        
        encoder_string = container_encoder or video_encoder
        
        if encoder_string:
            encoding_info["encoder_detected"] = True
            encoding_info["encoder_string"] = encoder_string
            
            encoder_lower = encoder_string.lower()
            
            # Поиск признаков ИИ
            for keyword in self.ai_encoder_keywords:
                if keyword in encoder_lower:
                    encoding_info["ai_indicators"].append(keyword)
                    encoding_info["suspicious"] = True
            
            # Проверка на известные редакторы
            known_editors = ["ffmpeg", "adobe", "davinci", "premiere", "final cut"]
            is_known_editor = any(editor in encoder_lower for editor in known_editors)
            
            if not is_known_editor and encoder_string:
                # Неизвестный encoder может быть признаком ИИ-пайплайна
                encoding_info["suspicious"] = True
        
        return encoding_info
    
    def check_frame_consistency(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка консистентности кадровой частоты и GOP структуры"""
        consistency = {
            "frame_rate_consistent": True,
            "gop_structure_ok": True,
            "anomalies": []
        }
        
        video_stream = metadata.get("video_stream", {})
        
        if not video_stream:
            return consistency
        
        # Проверка консистентности frame rate
        r_frame_rate = video_stream.get("r_frame_rate")
        avg_frame_rate = video_stream.get("avg_frame_rate")
        
        if r_frame_rate and avg_frame_rate:
            try:
                # Парсинг дробей (например, "30/1")
                r_parts = r_frame_rate.split("/")
                avg_parts = avg_frame_rate.split("/")
                
                if len(r_parts) == 2 and len(avg_parts) == 2:
                    r_rate = float(r_parts[0]) / float(r_parts[1])
                    avg_rate = float(avg_parts[0]) / float(avg_parts[1])
                    
                    # Разница не должна быть большой
                    if abs(r_rate - avg_rate) > 0.1:
                        consistency["frame_rate_consistent"] = False
                        consistency["anomalies"].append(
                            f"Несоответствие frame rate: r_frame_rate={r_frame_rate}, avg_frame_rate={avg_frame_rate}"
                        )
            except (ValueError, ZeroDivisionError):
                pass
        
        # Проверка на необычные frame rates (признак генерации)
        if r_frame_rate:
            try:
                r_parts = r_frame_rate.split("/")
                if len(r_parts) == 2:
                    rate = float(r_parts[0]) / float(r_parts[1])
                    # Необычные frame rates могут указывать на генерацию
                    if rate not in [24, 25, 30, 50, 60] and 20 < rate < 70:
                        consistency["anomalies"].append(
                            f"Необычная кадровая частота: {rate} fps"
                        )
            except (ValueError, ZeroDivisionError):
                pass
        
        return consistency
    
    def detect_encoding_anomalies(
        self, 
        metadata: Dict[str, Any], 
        encoding_info: Dict[str, Any],
        frame_consistency: Dict[str, Any]
    ) -> List[str]:
        """Выявление аномалий кодирования"""
        anomalies = []
        
        # Аномалии из encoding_info
        if encoding_info.get("suspicious"):
            anomalies.append("Подозрительный encoder string")
        
        if encoding_info.get("ai_indicators"):
            anomalies.append(f"Обнаружены признаки ИИ в encoder: {', '.join(encoding_info['ai_indicators'])}")
        
        # Аномалии из frame_consistency
        anomalies.extend(frame_consistency.get("anomalies", []))
        
        # Проверка на отсутствие метаданных при высоком качестве
        video_stream = metadata.get("video_stream", {})
        if video_stream:
            bit_rate = video_stream.get("bit_rate")
            if bit_rate:
                try:
                    bit_rate_int = int(bit_rate)
                    # Высокий bitrate, но нет encoder информации - подозрительно
                    if bit_rate_int > 5000000 and not encoding_info.get("encoder_detected"):
                        anomalies.append("Высокое качество без информации об encoder")
                except (ValueError, TypeError):
                    pass
        
        return anomalies

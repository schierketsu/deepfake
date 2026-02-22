# Deepfake Metadata Analyzer

Веб-сервис для анализа метаданных изображений и видео и выявления ИИ-модификаций.

## Описание

Сервис автоматически анализирует метаданные загруженных файлов (EXIF/XMP для изображений, метаданные контейнера для видео) и определяет вероятность того, что контент был создан или обработан с помощью нейросетей.

## Возможности

- **Анализ изображений**: EXIF, XMP, IPTC метаданные
- **Анализ видео**: метаданные контейнера, кодек, encoder strings, GOP структура
- **Анализ документов Word (.docx)**: извлечение всех изображений из файла и проверка каждого на признаки ИИ
- **Детекция ИИ**: поиск признаков использования ИИ-инструментов (Stable Diffusion, Midjourney, DALL·E, Sora и др.)
- **Генерация отчетов**: PDF и JSON форматы с визуальными индикаторами

## Технологический стек

### Backend
- Python 3.11+
- FastAPI
- Pillow, exifread, piexif - работа с изображениями
- ffmpeg-python - анализ видео
- reportlab - генерация PDF

### Frontend
- Vue 3
- Vite
- TailwindCSS
- Axios

## Установка и запуск

### Требования

- Python 3.11+
- Node.js 18+
- FFmpeg (для анализа видео)
- ExifTool (рекомендуется для полного извлечения метаданных)

#### Установка ExifTool

**Windows:**
1. Скачайте ExifTool с [официального сайта](https://exiftool.org/)
2. Распакуйте архив в папку проекта (например, `exiftool-13.48_64`)
3. Система автоматически найдет `exiftool(-k).exe` в папке проекта
4. Или добавьте путь к `exiftool.exe` в переменную PATH для глобального использования

**Linux:**
```bash
sudo apt-get install libimage-exiftool-perl
```

**macOS:**
```bash
brew install exiftool
```

Примечание: Если ExifTool не установлен, система будет использовать альтернативные методы (exifread, PIL), но извлечение метаданных будет менее полным.

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Сервис будет доступен по адресу `http://localhost:3000`

### Docker

```bash
docker-compose up
```

## Использование

1. Откройте веб-интерфейс
2. Загрузите изображение (JPEG, PNG, HEIC), видео (MP4, MOV, MKV) или документ Word (.docx)
3. Дождитесь завершения анализа (для .docx извлекаются и анализируются все изображения из документа)
4. Просмотрите результаты и экспортируйте отчет при необходимости

## API Endpoints

- `POST /api/analyze/image` - анализ изображения
- `POST /api/analyze/video` - анализ видео
- `POST /api/analyze/document` - анализ документа Word (.docx): извлечение изображений и проверка на ИИ
- `GET /api/health` - проверка статуса
- `GET /api/reports/{filename}` - получение PDF отчета

## Структура проекта

```
deepfake/
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── services/    # Бизнес-логика
│   │   └── models/      # Pydantic модели
│   └── requirements.txt
├── frontend/            # Vue.js frontend
│   ├── src/
│   │   ├── components/  # Vue компоненты
│   │   └── services/   # API клиент
│   └── package.json
└── docker-compose.yml
```

## Безопасность

- Файлы хранятся временно и автоматически удаляются после анализа
- Максимальный размер файла: 100MB
- Валидация MIME типов
- CORS настройки для frontend

## Лицензия

MIT

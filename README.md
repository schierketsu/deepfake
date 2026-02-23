# Анализ метаданных офисных документов

Веб-сервис для проверки метаданных документов Word (DOCX) и PowerPoint (PPTX): автор, даты, ревизии, встроенные изображения и их метаданные.

## Описание

Сервис загружает офисный файл (DOCX или PPTX), извлекает свойства документа из `docProps`, перечисляет встроенные изображения и при необходимости анализирует метаданные каждого изображения. Подходит для проверки происхождения документа (например, преподавателем).

## Возможности

- **DOCX и PPTX**: один эндпоинт для обоих форматов
- **Метаданные документа**: автор, последний редактор, даты создания и изменения, ревизия, приложение
- **Встроенные изображения**: список с вероятностью ИИ по каждому, раскрытие детальных EXIF/XMP по клику
- **Отчёты**: PDF и JSON

## Технологический стек

### Backend
- Python 3.11+
- FastAPI
- ExifTool (для метаданных изображений внутри документов)
- reportlab — генерация PDF

### Frontend
- Vue 3
- Vite
- Tailwind CSS
- Axios

## Установка и запуск

### Требования

- Python 3.11+
- Node.js 18+
- ExifTool (рекомендуется для метаданных встроенных изображений)

**Установка ExifTool:** [exiftool.org](https://exiftool.org/) или пакет `libimage-exiftool-perl` (Linux), `brew install exiftool` (macOS).

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

Интерфейс: `http://localhost:3000`

### Docker

```bash
docker-compose up
```

## Использование

1. Откройте веб-интерфейс.
2. Загрузите файл DOCX или PPTX.
3. Просмотрите метаданные документа и список изображений; при необходимости откройте подробности по изображению.
4. Скачайте отчёт в PDF или JSON.

## API

- `POST /api/analyze/document` — анализ документа (DOCX/PPTX)
- `GET /api/health` — статус сервиса
- `GET /api/reports/{filename}` — получение PDF-отчёта

## Структура проекта

```
deepfake/
├── backend/
│   ├── app/
│   │   ├── api/          # Маршруты API
│   │   ├── services/     # document_analyzer, report_generator, image_analyzer (для вложенных изображений)
│   │   └── models/       # Схемы ответов
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # Загрузка, отчёт, таблица метаданных
│   │   └── services/     # API-клиент
│   └── package.json
└── docker-compose.yml
```

## Безопасность

- Файлы обрабатываются во временной директории и удаляются после анализа.
- Максимальный размер файла: 100 MB.
- Поддерживаются только форматы DOCX и PPTX.

## Лицензия

MIT

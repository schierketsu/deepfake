# необманывай!

Пет-проект для конкурса (IT-Планета 2026, трек «Антидипфейк»). 
Суть простая: загружаешь **docx** или **pptx**, сервис смотрит метаданные документа и вложенных картинок, плюс даёт числовые оценки с помощью обученных моделей по **табличным** признакам (не по пикселям картинки). 

## Запуск локально

**Бэкенд** (из корня репозитория удобнее держать `artifacts/` и `ml/` рядом с `backend/`):

```bash
cd backend
pip install -r requirements.txt
set PYTHONPATH=..
uvicorn app.main:app --reload --port 8000
```

**Фронт:**

```bash
cd frontend
npm install
npm run dev
```

Сайт: http://localhost:3000.
Модели лежат в `artifacts/` (в git их нет — нужны свои `model.joblib` и при желании `model_docx.joblib`).
Обучение, датасеты, метрики — в `data/README.md`, `scripts/`, `docs/baseline_metrics.md`.

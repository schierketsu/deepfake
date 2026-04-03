# Проверка учебных документов (метаданные + ML по метаданным)

Веб-сервис анализирует **DOCX/PPTX**: свойства документа и **встроенные изображения**. Для каждой картинки считается:

- **`metadata_score`** — эвристический baseline по EXIF/XMP/C2PA и признакам файла ([`backend/app/services/ai_detector.py`](backend/app/services/ai_detector.py)).
- **`ml_metadata_score`** — вероятность «ИИ-генерации» по **табличным признакам метаданных** (обученная модель в `artifacts/model.joblib`). Содержимое пикселей не используется.
- **`final_score`** — слияние эвристики и ML ([`backend/app/services/score_fusion.py`](backend/app/services/score_fusion.py)); в API поле `ai_probability` совпадает с итогом.

Датасет для обучения строится по **происхождению файла** (real vs сгенерированный ИИ), без привязки к «сюжету» изображения.

Оценка **вероятностная**, не является юридическим доказательством.

## Запуск

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

## Data Science pipeline (только метаданные)

1. Положите изображения в [`data/raw/real/`](data/raw/real/) и [`data/raw/ai/`](data/raw/ai/) — классы по **источнику** файла, см. [`data/README.md`](data/README.md).
2. Соберите признаки: `python scripts/build_dataset.py` (через `ImageAnalyzer`, без пикселей).
3. Обучите модель: `python scripts/train_model.py` → [`artifacts/model.joblib`](artifacts/model.joblib)
4. При необходимости: переменная **`ML_MODEL_PATH`**

Метрики и сравнение подходов: [`docs/baseline_metrics.md`](docs/baseline_metrics.md)

EDA: [`notebooks/eda.ipynb`](notebooks/eda.ipynb)

## Структура репозитория

| Путь | Назначение |
|------|------------|
| `backend/` | FastAPI, эвристики, PDF-отчёты |
| `frontend/` | Vue 3 UI |
| `ml/` | Признаки метаданных и инференс |
| `scripts/` | Сбор датасета, обучение, оценка |
| `data/` | Сырые и обработанные данные |
| `artifacts/` | Обученные модели (локально, см. `.gitignore`) |

## Ограничения

- Метаданные могут быть удалены или неполны; модель опирается на доступные поля.
- Качество ML зависит от репрезентативности датасета по источникам файлов.

## Roadmap

- Расширение датасета и сравнение с XGBoost.
- Опционально: анализ **текста** документа для мультимодальной оценки.

Проект: **Антидипфейк: Вызов • IT-Планета 2026**

# Датасет

## Идея

Мы учим модель отличать **паттерны метаданных** у файлов разного **происхождения**:

- `raw/real/` — изображения **реального** происхождения (фото, скриншоты, экспорты без ИИ-генерации).
- `raw/ai/` — изображения, **сгенерированные ИИ** (Midjourney, DALL·E, Stable Diffusion и т.д.).

**«Тема» картинки (пейзаж, лицо, диаграмма) не важна** — важны метка класса и разнообразие источников. Признаки извлекаются только из метаданных (EXIF/XMP/C2PA, счётчики полей, ключевые слова), **без анализа пикселей**.

## Документы Word (текст → табличные признаки, NLP-слой)

Отдельный пайплайн для **полного файла .docx** (не вложенные картинки):

- `raw/documents/real/` — работы **без** заявленной ИИ-помощи в тексте (по вашему протоколу разметки).
- `raw/documents/ai/` — документы, где текст создан с существенным участием ИИ (по вашему протоколу).

Признаки: длины, доля уникальных слов, пунктуации и т.д. ([`ml/docx_text_features.py`](../ml/docx_text_features.py)) — **не эмбеддинги и не «понимание смысла»**, удобно для интерпретации на защите.

```bash
python scripts/build_dataset_docx.py
python scripts/train_model_docx.py
python scripts/evaluate_model.py --csv data/processed/docx_text_features.csv --model artifacts/model_docx.joblib --json-out artifacts/eval_docx.json
```

## Сборка признаков (изображения)

```bash
python scripts/build_dataset.py
```

Создаётся `data/processed/features.csv` с колонкой `label` (`0` = real, `1` = ai) и **только** признаками из [`ml/metadata_features.py`](../ml/metadata_features.py).

Требуется тот же стек, что и у backend (в т.ч. при необходимости ExifTool — см. `ImageAnalyzer`).

## Обучение модели

```bash
python scripts/train_model.py
```

Модель: `artifacts/model.joblib`. Backend подхватывает её автоматически (или задайте `ML_MODEL_PATH`).

Метрики обучения пишутся в `artifacts/training_metrics.json`.

## Оценка (изображения / общий скрипт)

```bash
python scripts/evaluate_model.py
python scripts/evaluate_model.py --cv 5 --json-out artifacts/evaluation_cv5.json
```

## Объём данных

Для первого baseline рекомендуется **300–1000** изображений в сумме по классам, по возможности сбалансированно.

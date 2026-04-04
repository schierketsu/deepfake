# Baseline и метрики качества

## Эвристический baseline (метаданные)

Реализован в [`backend/app/services/ai_detector.py`](../backend/app/services/ai_detector.py): правила по EXIF/XMP/C2PA и размерам. Итог до слияния с ML — поле **`metadata_score`** (0–100).

## ML по метаданным

Модель обучается на табличных признаках из [`ml/metadata_features.py`](../ml/metadata_features.py), собранных через [`scripts/build_dataset.py`](../scripts/build_dataset.py) (без признаков пикселей). В API это **`ml_metadata_score`**.

### Как сравнить

1. Соберите размеченный набор по **происхождению файла** (см. [`data/README.md`](../data/README.md)).
2. Обучите модель (`scripts/train_model.py`).
3. На одном тестовом сплите сравните:
   - только эвристику (`metadata_score`);
   - только ML (`ml_metadata_score`);
   - итог после слияния (`final_score`), см. [`backend/app/services/score_fusion.py`](../backend/app/services/score_fusion.py).

### Рекомендуемые метрики

| Метрика    | Зачем |
|-----------|--------|
| Precision | Меньше ложных обвинений в «ИИ» |
| Recall    | Не пропускать реально сгенерированные |
| F1        | Баланс |
| ROC-AUC   | Качество ранжирования по вероятности |
| PR-AUC    | Полезно при дисбалансе классов |

После обучения смотрите `artifacts/training_metrics.json`. Для оценки с кросс-валидацией: `python scripts/evaluate_model.py --cv 5`.

## ML по тексту DOCX (отдельная ветка)

Признаки из [`ml/docx_text_features.py`](../ml/docx_text_features.py), сборка [`scripts/build_dataset_docx.py`](../scripts/build_dataset_docx.py), обучение [`scripts/train_model_docx.py`](../scripts/train_model_docx.py). В API — **`doc_nlp_ml_score`** (только для Word). Это **статистика строки**, не семантика; сравнивайте с моделью по метаданным изображений на одних и тех же документах для сюжета защиты.

## Ограничения

Оценка **вероятностная**. Метаданные могут отсутствовать; сильные факты C2PA учитываются в слиянии приоритетно.

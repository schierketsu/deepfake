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

## Ограничения

Оценка **вероятностная**. Метаданные могут отсутствовать; сильные факты C2PA учитываются в слиянии приоритетно.

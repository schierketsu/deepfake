# Идентифицирующие материалы программы

## 1. Общие сведения

- Наименование программы: `Сервис анализа метаданных документов для выявления признаков использования генеративного искусственного интеллекта`.
- Область применения: первичная экспертная проверка документов в образовательной и прикладной деятельности.
- Поддерживаемые входные форматы: `DOCX`, `PPTX`.
- Основные языки программирования: `Python` (серверная и ML-логика), `JavaScript` (клиентская часть).

## 2. Перечень основных модулей

### 2.1 Backend (API и бизнес-логика)

- `backend/app/main.py` — инициализация FastAPI-приложения, CORS, подключение маршрутов.
- `backend/app/api/routes.py` — REST-эндпоинты, загрузка документа, запуск анализа, возврат PDF-отчета.
- `backend/app/services/document_analyzer.py` — анализ `DOCX/PPTX`, извлечение метаданных, обработка вложенных изображений.
- `backend/app/services/image_analyzer.py` — извлечение технических метаданных изображений.
- `backend/app/services/ai_detector.py` — эвристики и расчет вероятностной оценки признаков ИИ.
- `backend/app/services/score_fusion.py` — объединение эвристической и ML-оценки.
- `backend/app/services/report_generator.py` — формирование итогового PDF-отчета.
- `backend/app/ml_bridge.py` — безопасный мост между API и ML-пакетом.
- `backend/app/models/schemas.py` — Pydantic-схемы API-ответов.

### 2.2 ML-часть

- `ml/metadata_features.py` — извлечение и нормализация признаков по метаданным.
- `ml/inference.py` — инференс мета-модели (`model.joblib`) и получение оценки 0..100.
- `ml/docx_text.py` — извлечение текста из `DOCX`.
- `ml/docx_text_features.py` — вычисление текстовых признаков документа.
- `ml/inference_docx.py` — инференс текстовой `DOCX`-модели (`model_docx.joblib`) и оценка 0..100.

### 2.3 Frontend (веб-интерфейс)

- `frontend/src/services/api.js` — HTTP-клиент и вызов API анализа.
- `frontend/src/components/FileUpload.vue` — загрузка входного файла пользователем.
- `frontend/src/components/ReportView.vue` — отображение результатов анализа и переход к отчету.
- `frontend/src/components/MetadataTable.vue` — таблица технических метаданных.
- `frontend/src/components/ImageDetailPanel.vue` — детальный просмотр данных по вложенным изображениям.
- `frontend/src/App.vue`, `frontend/src/main.js` — сборка и инициализация клиентского приложения.

## 3. Фрагменты ключевого кода

Ниже приведены фрагменты, идентифицирующие ключевую логику работы программы.

### Фрагмент 1. Инициализация API-приложения
Файл: `backend/app/main.py`

```python
app = FastAPI(
    title="Анализ метаданных офисных документов",
    description="Проверка метаданных DOCX/PPTX: автор, даты, встроенные изображения и их метаданные",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root_router)
app.include_router(router, prefix="/api")
```

### Фрагмент 2. Точка входа анализа документа
Файл: `backend/app/api/routes.py`

```python
@router.post("/analyze/document", response_model=AnalysisResponse)
@router.post("/analyze/document/", response_model=AnalysisResponse)
async def analyze_document(file: UploadFile = File(...)):
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Файл слишком большой (максимум 100MB)")

    fn = (file.filename or "").lower()
    if not (fn.endswith(".docx") or fn.endswith(".pptx")):
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только форматы DOCX и PPTX",
        )

    doc_analyzer = DocumentAnalyzer()
    doc_result = doc_analyzer.analyze_document(temp_file)
```

### Фрагмент 3. Выделение признаков программной генерации документа
Файл: `backend/app/services/document_analyzer.py`

```python
def _attach_programmatic_generation_trace(document_metadata: Dict[str, Any]) -> None:
    creator = (document_metadata.get("creator") or "").strip()
    last_mod = (document_metadata.get("last_modified_by") or "").strip()
    description = (document_metadata.get("description") or "").strip()
    application = (document_metadata.get("application") or "").strip()
    company = (document_metadata.get("company") or "").strip()
    template = (document_metadata.get("template") or "").strip()

    blob = " ".join(x for x in (
        creator.lower(),
        last_mod.lower(),
        description.lower(),
        application.lower(),
        company.lower(),
        template.lower(),
    ) if x)

    present = (
        "python-docx" in blob
        or "pandoc" in blob
        or "apache poi" in blob
        or "docx4j" in blob
        or "aspose" in blob
    )

    document_metadata["generation_trace_present"] = present
```

### Фрагмент 4. Извлечение метаданных офисного документа и вложений
Файл: `backend/app/services/document_analyzer.py`

```python
def analyze_document(self, office_path: str) -> Dict[str, Any]:
    with zipfile.ZipFile(office_path, "r") as zf:
        archive_names = zf.namelist()
        document_type = self._detect_document_type(archive_names)
        document_metadata = self._extract_document_metadata(zf, document_type)

    media_prefix = self.DOCX_MEDIA_PREFIX if document_type == "word" else self.PPTX_MEDIA_PREFIX
    extracted_images = self._extract_images(office_path, media_prefix=media_prefix)
```

### Фрагмент 5. Обнаружение признаков ИИ и расчет вероятности
Файл: `backend/app/services/ai_detector.py`

```python
def detect_ai_signs(self, metadata: Dict[str, Any], file_type: str = "image") -> Dict[str, Any]:
    result = {
        "software_detected": [],
        "heuristics": {},
        "anomalies": [],
        "ai_probability": 0,
        "confidence": "low"
    }

    if file_type == "image":
        result = self._detect_image_ai_signs(metadata)
    elif file_type == "video":
        result = self._detect_video_ai_signs(metadata)

    result["_metadata_ref"] = metadata
    result["ai_probability"] = self.calculate_ai_probability(result)
    result["metadata_score"] = result["ai_probability"]
    result["confidence"] = self.generate_confidence_score(result, metadata)
    result.pop("_metadata_ref", None)
    return result
```

### Фрагмент 6. ML-инференс по метаданным
Файл: `ml/inference.py`

```python
def predict_metadata_ml_score(
    metadata: Optional[Dict[str, Any]],
    model_path: Optional[Path] = None,
) -> Tuple[Optional[int], bool, Dict[str, Any]]:
    path = model_path or default_model_path()
    if not path.is_file():
        return None, False, {"error": "model file missing"}

    model, feat_names = load_model(path)
    combined = extract_metadata_only_features(metadata)
    X = vectorize_metadata_features(combined, feat_names).reshape(1, -1)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        score = int(round(float(proba[1]) * 100))
    else:
        pred = model.predict(X)[0]
        score = int(round(float(pred) * 100)) if pred <= 1.0 else int(pred)
    return max(0, min(100, score)), True, {"ok": True}
```

### Фрагмент 7. Безопасный вызов ML из backend
Файл: `backend/app/ml_bridge.py`

```python
def predict_metadata_ml_safe(
    metadata: Optional[Dict[str, Any]],
) -> Tuple[Optional[int], bool]:
    try:
        from ml.inference import predict_metadata_ml_score
        score, ok, _dbg = predict_metadata_ml_score(metadata)
        return score, ok
    except Exception:
        return None, False
```

### Фрагмент 8. Вызов API с клиентской части
Файл: `frontend/src/services/api.js`

```javascript
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000,
  headers: {
    'Content-Type': 'multipart/form-data'
  }
})

export const analyzeDocument = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/api/analyze/document', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}
```

## 4. Краткое описание алгоритма работы

1. Пользователь загружает файл `DOCX` или `PPTX` через веб-интерфейс.
2. Сервер проверяет размер и тип файла, затем временно сохраняет документ для анализа.
3. Из документа извлекаются:
   - общие метаданные (`docProps/core.xml`, `docProps/app.xml`);
   - вложенные изображения из архивных разделов `word/media` или `ppt/media`.
4. Для каждого вложенного изображения извлекаются EXIF/XMP/C2PA-данные, применяются эвристики и ML-оценка.
5. По документу дополнительно может рассчитываться NLP-оценка (для `DOCX`).
6. Формируется агрегированный результат и генерируется PDF-отчет.

## 5. Состав файлов, рекомендуемых к приложению

Для раздела идентифицирующих материалов обычно достаточно:

- настоящий файл `docs/patent_identifying_materials.md` (или его экспорт в PDF);
- исходные тексты ключевых модулей:
  - `backend/app/main.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/document_analyzer.py`
  - `backend/app/services/ai_detector.py`
  - `backend/app/ml_bridge.py`
  - `ml/inference.py`
  - `frontend/src/services/api.js`

При необходимости объем материала увеличивается добавлением схем данных (`backend/app/models/schemas.py`) и генерации отчета (`backend/app/services/report_generator.py`).

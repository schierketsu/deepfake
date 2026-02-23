from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.api.routes import router
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Анализ метаданных офисных документов",
    description="Проверка метаданных DOCX/PPTX: автор, даты, встроенные изображения и их метаданные",
    version="1.0.0"
)

# CORS настройки для frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Сначала корневые пути (без /api), чтобы GET /routes не давал 404 от расширений браузера
root_router = APIRouter()

@root_router.get("/")
async def root():
    return {"message": "API анализа метаданных DOCX/PPTX", "version": "1.0.0"}

@root_router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@root_router.get("/routes", include_in_schema=False)
async def routes_list():
    return {
        "endpoints": [
            "GET /api/health",
            "GET /api/routes",
            "POST /api/analyze/document",
            "GET /api/reports/{filename}",
        ]
    }

app.include_router(root_router)
app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup_log():
    logger.info("API готов: GET /routes и GET /api/routes доступны")

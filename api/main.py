from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path
from db.session import init_db
from api.routes import router
from api.routes.cv_jobs import router as cv_jobs_router
from api.routers.application import router as visa_router
from api.routers.chat import router as chat_router
from api.routers.forms import router as forms_router
from api.routers.extract import router as extract_router
from api.routers.admin import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Visa Flow",
    description="Multi-agent visa processing system powered by Claude",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(cv_jobs_router, prefix="/api/v1")
app.include_router(visa_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(forms_router, prefix="/api")
app.include_router(extract_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="react-assets")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/cv-jobs")
def cv_jobs_page():
    return FileResponse(FRONTEND_DIR / "cv-jobs.html")

@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    return FileResponse(FRONTEND_DIR / "index.html")

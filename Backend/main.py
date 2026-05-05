import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

import app.config as config
from app.db import Base, engine
from app.middleware import APIKeyScrubMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from app.routes.auth import router as auth_router
from app.routes.fix import router as fix_router
from app.routes.index import router as index_router
from app.routes.pr import router as pr_router
from app.routes.settings import router as settings_router

import app.models_db  # noqa: F401  ensure models are registered before create_all

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("users")}
    if "repo_path" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN repo_path TEXT"))
        logger.info("Migrated: added repo_path column to users table")
    for col in ("github_repo_owner", "github_repo_name"):
        if col not in cols:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} VARCHAR(255)"))
            logger.info("Migrated: added %s column to users table", col)
    yield


app = FastAPI(
    title="AutoPatch AI",
    description="AI-powered code patch generation from bug tickets",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(APIKeyScrubMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    global_rpm=config.RATE_LIMIT_GLOBAL,
    llm_rpm=config.RATE_LIMIT_LLM,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
    allow_credentials=True,
)

app.include_router(auth_router, prefix="/api")
app.include_router(fix_router, prefix="/api")
app.include_router(index_router, prefix="/api")
app.include_router(pr_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "Frontend" / "dist"


@app.get("/health")
def health():
    return {"status": "ok"}


if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{path:path}")
    def serve_frontend(path: str):
        file = FRONTEND_DIST / path
        if file.is_file():
            return FileResponse(str(file))
        return FileResponse(str(FRONTEND_DIST / "index.html"))

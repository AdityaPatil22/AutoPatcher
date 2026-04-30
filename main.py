from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes.fix import router as fix_router
from app.routes.index import router as index_router
from app.routes.settings import router as settings_router

app = FastAPI(
    title="AutoPatch AI",
    description="AI-powered code patch generation from bug tickets",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fix_router, prefix="/api")
app.include_router(index_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

FRONTEND_DIST = Path(__file__).resolve().parent / "Frontend" / "dist"


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

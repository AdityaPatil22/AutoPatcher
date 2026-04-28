from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.fix import router as fix_router

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


@app.get("/health")
def health():
    return {"status": "ok"}

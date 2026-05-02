"""Application configuration loaded from environment variables."""

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "local")
LLM_MODEL: str = os.getenv("LLM_MODEL", "")
LOCAL_LLM_BASE_URL: str = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")

# --- Security / CORS ---
_origins_raw = os.getenv("ALLOWED_ORIGINS", "*").strip()
ALLOWED_ORIGINS: list[str] = (
    ["*"] if _origins_raw == "*"
    else [o.strip() for o in _origins_raw.split(",") if o.strip()]
)
RATE_LIMIT_GLOBAL: int = int(os.getenv("RATE_LIMIT_GLOBAL", "60"))
RATE_LIMIT_LLM: int = int(os.getenv("RATE_LIMIT_LLM", "10"))

# --- GitHub OAuth ---
GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE-ME-generate-a-fernet-key")
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

# --- Database ---
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/autopatch")

# --- Indexing ---
_default_repo = os.getenv("SAMPLE_REPO_PATH", "")
SAMPLE_REPO_PATH: Path | None = Path(_default_repo) if _default_repo else None
MAX_CONTEXT_FILES: int = int(os.getenv("MAX_CONTEXT_FILES", "3"))
CHROMA_PERSIST_DIR: Path = Path(
    os.getenv("CHROMA_PERSIST_DIR", str(Path(__file__).resolve().parent.parent.parent / ".chroma_index"))
)
CLONE_DIR: Path = Path(os.getenv("CLONE_DIR", str(Path(tempfile.gettempdir()) / "autopatch_clones")))

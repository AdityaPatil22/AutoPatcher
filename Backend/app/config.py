"""Application configuration loaded from environment variables."""

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
API_KEY: str = os.getenv("API_KEY", "")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
LLM_DAILY_LIMIT: int = int(os.getenv("LLM_DAILY_LIMIT", "5"))

# --- GitHub OAuth ---
GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
JWT_SECRET: str = os.getenv("JWT_SECRET", "juTlRdbN5JfIAPkrfU8JGqeyw2mhSBgdZBL3b_bmCiY=")
FERNET_KEY: str = os.getenv("FERNET_KEY", "QRiIDb8T9n_ILVamKlahwgVhqKhBWBw_ceORWKMEXPk=")
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

# --- Security / CORS ---
# allow_credentials=True is required (session cookie is cross-origin between frontend/backend
# deployments), and the CORS spec forbids combining that with a "*" origin — so "*" is rejected
# rather than silently degraded into "reflect any origin" (which is what Starlette does).
_origins_raw = os.getenv("ALLOWED_ORIGINS", "").strip()
if _origins_raw == "*":
    raise RuntimeError(
        "ALLOWED_ORIGINS=* is not allowed with credentialed CORS requests. "
        "Set it to a comma-separated list of exact origins (e.g. your frontend's URL)."
    )
ALLOWED_ORIGINS: list[str] = (
    [o.strip() for o in _origins_raw.split(",") if o.strip()]
    if _origins_raw else [FRONTEND_URL]
)
RATE_LIMIT_GLOBAL: int = int(os.getenv("RATE_LIMIT_GLOBAL", "100"))
RATE_LIMIT_LLM: int = int(os.getenv("RATE_LIMIT_LLM", "10"))

# --- Database ---
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/autopatch")

# --- Indexing ---
REPO_PATH: Path | None = None  # legacy; per-user repo_path is stored in DB
MAX_CONTEXT_FILES: int = int(os.getenv("MAX_CONTEXT_FILES", "3"))
CHROMA_PERSIST_DIR: Path = Path(
    os.getenv("CHROMA_PERSIST_DIR", str(Path(__file__).resolve().parent.parent.parent / ".chroma_index"))
)
CLONE_DIR: Path = Path(os.getenv("CLONE_DIR", str(Path(tempfile.gettempdir()) / "autopatch_clones")))

# --- ChromaDB client mode ---
# "local" = PersistentClient on disk (default), "cloud" = Chroma Cloud, "server" = self-hosted HttpClient
CHROMA_MODE: str = os.getenv("CHROMA_MODE", "local")
CHROMA_API_KEY: str = os.getenv("CHROMA_API_KEY", "")
CHROMA_TENANT: str = os.getenv("CHROMA_TENANT", "")
CHROMA_DATABASE: str = os.getenv("CHROMA_DATABASE", "")
CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))

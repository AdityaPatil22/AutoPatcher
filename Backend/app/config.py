"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "local")
LLM_MODEL: str = os.getenv("LLM_MODEL", "")

LOCAL_LLM_BASE_URL: str = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")

_default_repo = os.getenv("SAMPLE_REPO_PATH", "")
SAMPLE_REPO_PATH: Path | None = Path(_default_repo) if _default_repo else None

SEARCH_MODE: str = os.getenv("SEARCH_MODE", "hybrid")

MAX_CONTEXT_FILES: int = int(os.getenv("MAX_CONTEXT_FILES", "3"))

CHROMA_PERSIST_DIR: Path = Path(
    os.getenv("CHROMA_PERSIST_DIR", str(Path(__file__).resolve().parent.parent.parent / ".chroma_index"))
)

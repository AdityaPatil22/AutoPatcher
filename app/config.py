import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

LOCAL_LLM_BASE_URL: str = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")

SAMPLE_REPO_PATH: Path = Path(
    os.getenv("SAMPLE_REPO_PATH", str(Path(__file__).resolve().parent.parent / "sample_repo"))
)

SEARCH_MODE: str = os.getenv("SEARCH_MODE", "hybrid")

CHROMA_PERSIST_DIR: Path = Path(
    os.getenv("CHROMA_PERSIST_DIR", str(Path(__file__).resolve().parent.parent / ".chroma_index"))
)

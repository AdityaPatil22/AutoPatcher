import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

SAMPLE_REPO_PATH: Path = Path(
    os.getenv("SAMPLE_REPO_PATH", str(Path(__file__).resolve().parent.parent / "sample_repo"))
)

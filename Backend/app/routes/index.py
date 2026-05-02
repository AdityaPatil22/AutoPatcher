"""Routes for repository indexing and file tree retrieval."""

import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException

import app.config as config
from app.models import IndexRequest
from app.services.indexer import get_index_stats, get_indexed_files, index_repository
from app.utils.tree import build_file_tree

logger = logging.getLogger(__name__)

router = APIRouter(tags=["index"])

_GITHUB_URL_RE = re.compile(r"^https://github\.com/[\w.\-]+/[\w.\-]+/?$")


def _clone_github_repo(github_url: str) -> Path:
    """Clone a public GitHub repo (shallow) into CLONE_DIR, cleaning up any prior clone."""
    url = github_url.rstrip("/")
    if not _GITHUB_URL_RE.match(url):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL. Expected https://github.com/owner/repo")

    parts = url.rstrip("/").split("/")
    repo_name = parts[-1]

    clone_dir = config.CLONE_DIR
    clone_dir.mkdir(parents=True, exist_ok=True)

    target = clone_dir / repo_name
    if target.exists():
        shutil.rmtree(target)

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", f"{url}.git", str(target)],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.CalledProcessError as e:
        logger.error("git clone failed: %s", e.stderr)
        raise HTTPException(status_code=400, detail=f"Failed to clone repository: {e.stderr.strip()}")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Clone timed out. The repository may be too large.")

    return target


@router.post("/index")
def index_repo(req: IndexRequest):
    """Index a repository from a local path or a GitHub URL."""
    if req.github_url:
        repo = _clone_github_repo(req.github_url)
    else:
        repo = Path(req.repo_path).expanduser().resolve()
        if not repo.is_dir():
            raise HTTPException(status_code=400, detail=f"Directory not found: {repo}")

    config.SAMPLE_REPO_PATH = repo

    result = index_repository(repo)
    return {
        "status": "ok",
        "files_indexed": result["files_indexed"],
        "chunks_created": result["chunks_created"],
        "message": f"Indexed {result['files_indexed']} files ({result['chunks_created']} chunks)",
    }


@router.get("/index/status")
def index_status():
    """Return current index stats (whether indexed and chunk count)."""
    return get_index_stats()


@router.get("/index/files")
def index_files():
    """Return the indexed file tree with relative paths."""
    raw_paths = get_indexed_files()
    if not raw_paths:
        return {"tree": [], "total_files": 0}

    prefix = os.path.commonpath(raw_paths) if len(raw_paths) > 1 else str(Path(raw_paths[0]).parent)
    prefix = prefix.rstrip("/") + "/"

    relative = [p[len(prefix):] if p.startswith(prefix) else p for p in raw_paths]

    tree = build_file_tree(sorted(relative))
    return {"tree": tree, "total_files": len(raw_paths), "root": prefix}

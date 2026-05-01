"""Routes for repository indexing and file tree retrieval."""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

import app.config as config
from app.models import IndexRequest
from app.services.indexer import get_index_stats, get_indexed_files, index_repository
from app.utils.tree import build_file_tree

router = APIRouter(tags=["index"])


@router.post("/index")
def index_repo(req: IndexRequest):
    """Index a repository directory for code search."""
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

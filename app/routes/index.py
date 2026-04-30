from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import app.config as config
from app.services.indexer import get_index_stats, index_repository

router = APIRouter(tags=["index"])


class IndexRequest(BaseModel):
    repo_path: str = Field(..., min_length=1)


@router.post("/index")
def index_repo(req: IndexRequest):
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
    return get_index_stats()

from fastapi import APIRouter

from app.services.indexer import get_index_stats, index_repository

router = APIRouter(tags=["index"])


@router.post("/index")
def index_repo():
    result = index_repository()
    return {
        "status": "ok",
        "files_indexed": result["files_indexed"],
        "chunks_created": result["chunks_created"],
    }


@router.get("/index/status")
def index_status():
    return get_index_stats()

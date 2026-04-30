import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import app.config as config
from app.services.indexer import get_index_stats, get_indexed_files, index_repository

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


@router.get("/index/files")
def index_files():
    raw_paths = get_indexed_files()
    if not raw_paths:
        return {"tree": [], "total_files": 0}

    prefix = os.path.commonpath(raw_paths) if len(raw_paths) > 1 else str(Path(raw_paths[0]).parent)
    prefix = prefix.rstrip("/") + "/"

    relative = [p[len(prefix):] if p.startswith(prefix) else p for p in raw_paths]

    tree = _build_tree(sorted(relative))
    return {"tree": tree, "total_files": len(raw_paths), "root": prefix}


def _build_tree(paths: list[str]) -> list[dict]:
    root: dict = {}
    for path in paths:
        parts = path.split("/")
        node = root
        for part in parts:
            if part not in node:
                node[part] = {}
            node = node[part]

    def to_list(node: dict, name: str = "") -> list[dict]:
        items = []
        for key, children in sorted(node.items()):
            if children:
                items.append({
                    "name": key,
                    "type": "folder",
                    "children": to_list(children, key),
                })
            else:
                items.append({"name": key, "type": "file"})
        return items

    return to_list(root)

import hashlib
import os
from pathlib import Path

import chromadb

from app.config import CHROMA_PERSIST_DIR
from app.services.context import SKIP_DIRS, SUPPORTED_EXTENSIONS

CHUNK_SIZE = 60
CHUNK_OVERLAP = 10


def _get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    return client.get_or_create_collection(
        name="autopatch_code",
        metadata={"hnsw:space": "cosine"},
    )


def _chunk_file(content: str, filepath: str) -> list[dict]:
    lines = content.split("\n")
    chunks = []

    if len(lines) <= CHUNK_SIZE:
        chunks.append({
            "content": content,
            "filepath": filepath,
            "start_line": 1,
            "end_line": len(lines),
        })
    else:
        for start in range(0, len(lines), CHUNK_SIZE - CHUNK_OVERLAP):
            end = min(start + CHUNK_SIZE, len(lines))
            chunk_content = "\n".join(lines[start:end])
            chunks.append({
                "content": chunk_content,
                "filepath": filepath,
                "start_line": start + 1,
                "end_line": end,
            })
            if end == len(lines):
                break

    return chunks


def _make_chunk_id(filepath: str, start_line: int) -> str:
    raw = f"{filepath}:{start_line}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def index_repository(repo_path: Path) -> dict:
    collection = _get_collection()

    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)

    ids = []
    documents = []
    metadatas = []
    files_indexed = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            ext = Path(filename).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            filepath = Path(root) / filename
            try:
                content = filepath.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue

            chunks = _chunk_file(content, str(filepath))
            for chunk in chunks:
                chunk_id = _make_chunk_id(chunk["filepath"], chunk["start_line"])
                ids.append(chunk_id)
                documents.append(chunk["content"])
                metadatas.append({
                    "filepath": chunk["filepath"],
                    "filename": filename,
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                })

            files_indexed += 1

    if ids:
        batch_size = 5000
        for i in range(0, len(ids), batch_size):
            collection.add(
                ids=ids[i : i + batch_size],
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

    return {
        "files_indexed": files_indexed,
        "chunks_created": len(ids),
    }


def search_semantic(query: str, top_k: int = 10) -> list[dict]:
    collection = _get_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
    )

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "filepath": results["metadatas"][0][i]["filepath"],
            "filename": results["metadatas"][0][i]["filename"],
            "distance": results["distances"][0][i],
            "content": results["documents"][0][i],
            "start_line": results["metadatas"][0][i]["start_line"],
            "end_line": results["metadatas"][0][i]["end_line"],
        })

    return hits


def is_indexed() -> bool:
    try:
        return _get_collection().count() > 0
    except Exception:
        return False


def get_index_stats() -> dict:
    try:
        collection = _get_collection()
        return {"indexed": collection.count() > 0, "total_chunks": collection.count()}
    except Exception:
        return {"indexed": False, "total_chunks": 0}


def get_indexed_files() -> list[str]:
    try:
        collection = _get_collection()
        if collection.count() == 0:
            return []
        result = collection.get(include=["metadatas"])
        paths = sorted({m["filepath"] for m in result["metadatas"]})
        return paths
    except Exception:
        return []

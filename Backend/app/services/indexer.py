"""ChromaDB-based code indexing and semantic search."""

import hashlib
import os
from pathlib import Path

import chromadb

from app import config
from app.constants import SKIP_DIRS, SUPPORTED_EXTENSIONS

CHUNK_SIZE = 60
CHUNK_OVERLAP = 10

_chroma_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    """Return a cached ChromaDB client based on CHROMA_MODE."""
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client

    mode = config.CHROMA_MODE

    if mode == "cloud":
        _chroma_client = chromadb.CloudClient(
            tenant=config.CHROMA_TENANT,
            database=config.CHROMA_DATABASE,
            api_key=config.CHROMA_API_KEY,
        )
    elif mode == "server":
        _chroma_client = chromadb.HttpClient(
            host=config.CHROMA_HOST,
            port=config.CHROMA_PORT,
        )
    else:
        _chroma_client = chromadb.PersistentClient(path=str(config.CHROMA_PERSIST_DIR))

    return _chroma_client


def _get_collection(user_id: int):
    """Get or create the per-user ChromaDB collection for code chunks."""
    return _get_client().get_or_create_collection(
        name=f"autopatch_code_{user_id}",
        metadata={"hnsw:space": "cosine"},
    )


def _chunk_file(content: str, filepath: str) -> list[dict]:
    """Split a file's content into overlapping line-based chunks for embedding."""
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
    """Generate a deterministic short hash ID for a file chunk."""
    raw = f"{filepath}:{start_line}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def index_repository(repo_path: Path, user_id: int) -> dict:
    """Index all supported files in a repository into ChromaDB for semantic search."""
    collection = _get_collection(user_id)

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


def search_semantic(query: str, user_id: int, top_k: int = 10) -> list[dict]:
    """Query ChromaDB for the top-k most similar code chunks to the query text."""
    collection = _get_collection(user_id)

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


def clear_index(user_id: int) -> None:
    """Delete all indexed chunks for a user from ChromaDB."""
    collection = _get_collection(user_id)
    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)


def is_indexed(user_id: int) -> bool:
    """Check whether any code has been indexed in ChromaDB for this user."""
    try:
        return _get_collection(user_id).count() > 0
    except Exception:
        return False


def is_index_stale(user_id: int) -> bool:
    """Return True when Chroma has indexed paths but none exist on disk."""
    paths = get_indexed_files(user_id)
    if not paths:
        return False
    return not any(Path(p).exists() for p in paths)


def get_index_stats(user_id: int) -> dict:
    """Return index status and total chunk count for this user."""
    try:
        collection = _get_collection(user_id)
        indexed = collection.count() > 0
        return {
            "indexed": indexed,
            "total_chunks": collection.count(),
            "stale": is_index_stale(user_id) if indexed else False,
        }
    except Exception:
        return {"indexed": False, "total_chunks": 0, "stale": False}


def get_indexed_files(user_id: int) -> list[str]:
    """Return a sorted list of all indexed file paths for this user."""
    try:
        collection = _get_collection(user_id)
        if collection.count() == 0:
            return []
        result = collection.get(include=["metadatas"])
        paths = sorted({m["filepath"] for m in result["metadatas"]})
        return paths
    except Exception:
        return []

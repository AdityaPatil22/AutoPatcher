"""Orchestrates hybrid code search with fallback chains."""

import os
from pathlib import Path

import app.config as config
from app.constants import SKIP_DIRS
from app.services.search_keyword import extract_file_references, search_files
from app.services.search_semantic import search_files_hybrid


def get_top_contexts(
    query: str,
    file_hint: str | None = None,
    max_files: int | None = None,
    *,
    user_id: int,
    repo_path: str | None = None,
) -> list[dict]:
    """Return the top matching source files for a query, using the configured search strategy with fallbacks."""
    if max_files is None:
        max_files = config.MAX_CONTEXT_FILES

    results = _search_with_fallback(query, file_hint, user_id=user_id, repo_path=repo_path)

    direct_hits = _find_referenced_files(query, user_id=user_id)
    if direct_hits:
        seen_paths = {r["path"] for r in results}
        for hit in direct_hits:
            if hit["path"] not in seen_paths:
                results.insert(0, hit)
            else:
                for r in results:
                    if r["path"] == hit["path"]:
                        r["score"] = max(r["score"], hit["score"])
        results.sort(key=lambda x: x["score"], reverse=True)

    return results[:max_files]


def _search_with_fallback(
    query: str,
    file_hint: str | None,
    *,
    user_id: int,
    repo_path: str | None = None,
) -> list[dict]:
    """Run hybrid search, falling back through hint removal and keyword search."""
    results = search_files_hybrid(query, file_hint, user_id=user_id, repo_path=repo_path)

    if not results and file_hint:
        results = search_files_hybrid(query, user_id=user_id, repo_path=repo_path)

    if not results:
        results = search_files(query, file_hint, repo_path=repo_path)
        if not results and file_hint:
            results = search_files(query, repo_path=repo_path)

    return results


def _find_referenced_files(query: str, *, user_id: int) -> list[dict]:
    """Directly locate files mentioned by path in the query by walking the indexed repository."""
    file_refs = extract_file_references(query)
    if not file_refs:
        return []

    from app.services.indexer import get_indexed_files
    indexed = get_indexed_files(user_id)
    if not indexed:
        return []
    repo_path = os.path.commonpath(indexed)

    found = []
    for ref in file_refs:
        ref_base = Path(ref).name

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for filename in files:
                if filename == ref_base:
                    filepath = Path(root) / filename
                    fp_str = str(filepath)
                    if ref.count("/") > 0 and ref.lower() not in fp_str.lower():
                        continue
                    try:
                        content = filepath.read_text(encoding="utf-8")
                    except (FileNotFoundError, UnicodeDecodeError):
                        continue
                    found.append({
                        "path": fp_str,
                        "filename": filename,
                        "content": content,
                        "score": 2000,
                    })

    return found

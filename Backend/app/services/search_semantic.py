"""Semantic and hybrid code search using ChromaDB vector embeddings."""

from pathlib import Path

from app.services.search_keyword import extract_file_references, search_files


def search_files_semantic(query: str, file_hint: str | None = None, *, user_id: int) -> list[dict]:
    """Search indexed files by vector similarity, with score boosting for referenced filenames."""
    from app.services.indexer import search_semantic

    hits = search_semantic(query, user_id, top_k=10)
    if not hits:
        return []

    file_refs = extract_file_references(query)

    seen = {}
    for hit in hits:
        fp = hit["filepath"]
        if file_hint and file_hint.lower() not in hit["filename"].lower():
            continue
        if fp not in seen or hit["distance"] < seen[fp]["distance"]:
            seen[fp] = hit

    results = []
    for fp, hit in seen.items():
        try:
            full_content = Path(fp).read_text(encoding="utf-8")
        except (FileNotFoundError, UnicodeDecodeError):
            continue

        score = max(0, 2 - hit["distance"])

        if file_refs:
            fp_lower = fp.lower()
            fname_lower = hit["filename"].lower()
            for ref in file_refs:
                ref_lower = ref.lower()
                ref_base = Path(ref).name.lower()
                if ref_base == fname_lower or ref_lower in fp_lower or fp_lower.endswith(ref_lower):
                    score += 1000

        results.append({
            "path": fp,
            "filename": hit["filename"],
            "content": full_content,
            "score": score,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def search_files_hybrid(
    query: str,
    file_hint: str | None = None,
    *,
    user_id: int,
    repo_path: str | None = None,
) -> list[dict]:
    """Merge keyword and semantic search results with weighted scoring (40% keyword, 60% semantic)."""
    keyword_results = search_files(query, file_hint, repo_path=repo_path)
    semantic_results = search_files_semantic(query, file_hint, user_id=user_id)

    if not semantic_results:
        return keyword_results
    if not keyword_results:
        return semantic_results

    max_kw = max(r["score"] for r in keyword_results)
    kw_scores = {}
    for r in keyword_results:
        kw_scores[r["path"]] = {
            **r,
            "norm_score": r["score"] / max_kw if max_kw > 0 else 0,
        }

    max_sem = max(r["score"] for r in semantic_results)
    sem_scores = {}
    for r in semantic_results:
        sem_scores[r["path"]] = {
            **r,
            "norm_score": r["score"] / max_sem if max_sem > 0 else 0,
        }

    all_paths = set(kw_scores.keys()) | set(sem_scores.keys())
    merged = []
    for path in all_paths:
        kw = kw_scores.get(path, {}).get("norm_score", 0)
        sem = sem_scores.get(path, {}).get("norm_score", 0)
        combined_score = 0.4 * kw + 0.6 * sem

        base = sem_scores.get(path) or kw_scores.get(path)
        merged.append({
            "path": base["path"],
            "filename": base["filename"],
            "content": base["content"],
            "score": combined_score,
        })

    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged

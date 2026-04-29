import os
from pathlib import Path

from app.config import MAX_CONTEXT_FILES, SAMPLE_REPO_PATH, SEARCH_MODE

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".swift", ".kt", ".vue", ".svelte",
}

SKIP_DIRS = {
    "node_modules", ".next", "__pycache__", ".git", "dist", "build",
    ".venv", "venv", "env", ".tox", ".mypy_cache", ".pytest_cache",
    "coverage", ".nuxt", ".output", "out", "target", "bin", "obj",
}


def search_files(query: str, file_hint: str | None = None) -> list[dict]:
    keywords = _extract_keywords(query)
    results = []

    for root, dirs, files in os.walk(SAMPLE_REPO_PATH):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            ext = Path(filename).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            filepath = Path(root) / filename

            if file_hint and file_hint.lower() not in filename.lower():
                continue

            content = filepath.read_text(encoding="utf-8")
            score = _score_relevance(content, keywords)

            if score > 0:
                results.append({
                    "path": str(filepath),
                    "filename": filename,
                    "content": content,
                    "score": score,
                })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def search_files_semantic(query: str, file_hint: str | None = None) -> list[dict]:
    from app.services.indexer import search_semantic

    hits = search_semantic(query, top_k=10)
    if not hits:
        return []

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
        results.append({
            "path": fp,
            "filename": hit["filename"],
            "content": full_content,
            "score": score,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def search_files_hybrid(query: str, file_hint: str | None = None) -> list[dict]:
    keyword_results = search_files(query, file_hint)
    semantic_results = search_files_semantic(query, file_hint)

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


def get_best_context(query: str, file_hint: str | None = None) -> dict:
    if SEARCH_MODE == "semantic":
        results = search_files_semantic(query, file_hint)
    elif SEARCH_MODE == "hybrid":
        results = search_files_hybrid(query, file_hint)
    else:
        results = search_files(query, file_hint)

    if not results and file_hint:
        if SEARCH_MODE == "semantic":
            results = search_files_semantic(query)
        elif SEARCH_MODE == "hybrid":
            results = search_files_hybrid(query)
        else:
            results = search_files(query)

    if not results and SEARCH_MODE != "keyword":
        results = search_files(query, file_hint)
        if not results and file_hint:
            results = search_files(query)

    if results:
        return results[0]
    return {"path": "", "filename": "", "content": "No relevant code found.", "score": 0}


def get_top_contexts(
    query: str,
    file_hint: str | None = None,
    max_files: int | None = None,
) -> list[dict]:
    if max_files is None:
        max_files = MAX_CONTEXT_FILES

    if SEARCH_MODE == "semantic":
        results = search_files_semantic(query, file_hint)
    elif SEARCH_MODE == "hybrid":
        results = search_files_hybrid(query, file_hint)
    else:
        results = search_files(query, file_hint)

    if not results and file_hint:
        if SEARCH_MODE == "semantic":
            results = search_files_semantic(query)
        elif SEARCH_MODE == "hybrid":
            results = search_files_hybrid(query)
        else:
            results = search_files(query)

    if not results and SEARCH_MODE != "keyword":
        results = search_files(query, file_hint)
        if not results and file_hint:
            results = search_files(query)

    return results[:max_files]


def _extract_keywords(text: str) -> list[str]:
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "it", "its", "this", "that",
        "these", "those", "i", "we", "you", "he", "she", "they", "me", "him",
        "her", "us", "them", "my", "your", "his", "our", "their", "what",
        "which", "who", "whom", "when", "where", "why", "how", "not", "no",
        "nor", "but", "and", "or", "if", "then", "else", "for", "to", "from",
        "with", "in", "on", "at", "by", "of", "as", "into", "about", "after",
        "before", "between", "through", "during", "above", "below",
    }
    words = text.lower().split()
    return [w.strip(".,!?;:'\"()[]{}") for w in words if w.lower() not in stop_words and len(w) > 2]


def _score_relevance(content: str, keywords: list[str]) -> int:
    content_lower = content.lower()
    score = 0
    for keyword in keywords:
        count = content_lower.count(keyword.lower())
        score += count
    return score

import os
from pathlib import Path

import app.config as config

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
    if not config.SAMPLE_REPO_PATH:
        return []

    keywords = _extract_keywords(query)
    file_refs = _extract_file_references(query)
    results = []

    for root, dirs, files in os.walk(config.SAMPLE_REPO_PATH):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            ext = Path(filename).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            filepath = Path(root) / filename

            if file_hint and file_hint.lower() not in filename.lower():
                continue

            content = filepath.read_text(encoding="utf-8")
            score = _score_relevance(content, keywords, str(filepath), file_refs)

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

    file_refs = _extract_file_references(query)

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
    if config.SEARCH_MODE == "semantic":
        results = search_files_semantic(query, file_hint)
    elif config.SEARCH_MODE == "hybrid":
        results = search_files_hybrid(query, file_hint)
    else:
        results = search_files(query, file_hint)

    if not results and file_hint:
        if config.SEARCH_MODE == "semantic":
            results = search_files_semantic(query)
        elif config.SEARCH_MODE == "hybrid":
            results = search_files_hybrid(query)
        else:
            results = search_files(query)

    if not results and config.SEARCH_MODE != "keyword":
        results = search_files(query, file_hint)
        if not results and file_hint:
            results = search_files(query)

    if results:
        return results[0]
    return {"path": "", "filename": "", "content": "No relevant code found.", "score": 0}


def _find_referenced_files(query: str) -> list[dict]:
    """Directly locate files mentioned by path in the query text."""
    file_refs = _extract_file_references(query)
    if not file_refs or not config.CHROMA_PERSIST_DIR:
        return []

    from app.services.indexer import get_indexed_files
    indexed = get_indexed_files()
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


def get_top_contexts(
    query: str,
    file_hint: str | None = None,
    max_files: int | None = None,
) -> list[dict]:
    if max_files is None:
        max_files = config.MAX_CONTEXT_FILES

    if config.SEARCH_MODE == "semantic":
        results = search_files_semantic(query, file_hint)
    elif config.SEARCH_MODE == "hybrid":
        results = search_files_hybrid(query, file_hint)
    else:
        results = search_files(query, file_hint)

    if not results and file_hint:
        if config.SEARCH_MODE == "semantic":
            results = search_files_semantic(query)
        elif config.SEARCH_MODE == "hybrid":
            results = search_files_hybrid(query)
        else:
            results = search_files(query)

    if not results and config.SEARCH_MODE != "keyword":
        results = search_files(query, file_hint)
        if not results and file_hint:
            results = search_files(query)

    direct_hits = _find_referenced_files(query)
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


def _extract_file_references(text: str) -> list[str]:
    """Extract file path or filename references from bug description text."""
    import re
    patterns = [
        re.compile(r'[\w./\-\[\]]+\.(?:' + '|'.join(
            ext.lstrip('.') for ext in SUPPORTED_EXTENSIONS
        ) + r')', re.IGNORECASE),
    ]
    refs = []
    for pat in patterns:
        for match in pat.finditer(text):
            refs.append(match.group())
    return refs


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


def _score_relevance(content: str, keywords: list[str], filepath: str = "", file_refs: list[str] | None = None) -> int:
    content_lower = content.lower()
    score = 0
    for keyword in keywords:
        count = content_lower.count(keyword.lower())
        score += count

    if file_refs and filepath:
        filepath_lower = filepath.lower()
        filename_lower = Path(filepath).name.lower()
        for ref in file_refs:
            ref_lower = ref.lower()
            ref_base = Path(ref).name.lower()
            if ref_base == filename_lower or ref_lower in filepath_lower or filepath_lower.endswith(ref_lower):
                score += 1000

    return score

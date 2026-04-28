import os
from pathlib import Path

from app.config import SAMPLE_REPO_PATH


def search_files(query: str, file_hint: str | None = None) -> list[dict]:
    """
    Search sample_repo for files relevant to the bug description.
    Uses keyword matching — intentionally simple for MVP.
    """
    keywords = _extract_keywords(query)
    results = []

    for root, _, files in os.walk(SAMPLE_REPO_PATH):
        for filename in files:
            if not filename.endswith(".py"):
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


def get_best_context(query: str, file_hint: str | None = None) -> dict:
    """Return the single most relevant file for the given bug description."""
    results = search_files(query, file_hint)
    if not results:
        all_files = search_files(query)
        if all_files:
            return all_files[0]
        return {"path": "", "filename": "", "content": "No relevant code found.", "score": 0}
    return results[0]


def _extract_keywords(text: str) -> list[str]:
    """Pull meaningful keywords from the query, filtering noise."""
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
    """Score how relevant a file's content is based on keyword matches."""
    content_lower = content.lower()
    score = 0
    for keyword in keywords:
        count = content_lower.count(keyword.lower())
        score += count
    return score

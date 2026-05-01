"""Keyword-based code search with relevance scoring and file reference extraction."""

import os
import re
from pathlib import Path

import app.config as config
from app.constants import SKIP_DIRS, SUPPORTED_EXTENSIONS


def search_files(query: str, file_hint: str | None = None) -> list[dict]:
    """Walk the repo and score files by keyword relevance, optionally filtered by filename hint."""
    if not config.SAMPLE_REPO_PATH:
        return []

    keywords = extract_keywords(query)
    file_refs = extract_file_references(query)
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
            score = score_relevance(content, keywords, str(filepath), file_refs)

            if score > 0:
                results.append({
                    "path": str(filepath),
                    "filename": filename,
                    "content": content,
                    "score": score,
                })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def extract_file_references(text: str) -> list[str]:
    """Extract file path or filename references from text using supported extensions."""
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


def extract_keywords(text: str) -> list[str]:
    """Split text into meaningful keywords after removing common stop words."""
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


def score_relevance(content: str, keywords: list[str], filepath: str = "", file_refs: list[str] | None = None) -> int:
    """Score a file's relevance based on keyword frequency and file reference matches."""
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

import re


def _to_str(val) -> str:
    if isinstance(val, list):
        return "\n".join(str(item) for item in val)
    return str(val) if val else ""


def _strip_line_numbers(text: str) -> str:
    """Remove line number prefixes the LLM may have copied from the prompt."""
    lines = text.split("\n")
    stripped = []
    for line in lines:
        cleaned = re.sub(r"^\s*\d+\s*\|\s?", "", line)
        stripped.append(cleaned)
    if stripped != lines:
        return "\n".join(stripped)
    return text


def apply_changes(content: str, changes: list[dict]) -> str:
    result = content
    for change in changes:
        original = _to_str(change.get("original", ""))
        modified = _to_str(change.get("modified", ""))
        if not original:
            continue

        original = _strip_line_numbers(original)
        modified = _strip_line_numbers(modified)

        if original in result:
            result = result.replace(original, modified, 1)
            continue

        replaced = _fuzzy_replace(result, original, modified)
        if replaced is not None:
            result = replaced

    return result


def _normalize(line: str) -> str:
    return line.strip().replace("\t", "    ")


def _fuzzy_replace(content: str, original: str, modified: str) -> str | None:
    orig_lines = [l for l in original.strip().split("\n") if l.strip()]
    if not orig_lines:
        return None

    content_lines = content.split("\n")
    mod_lines = modified.split("\n") if modified else []

    # Pass 1: exact match on stripped lines
    for i in range(len(content_lines) - len(orig_lines) + 1):
        window = content_lines[i : i + len(orig_lines)]
        if all(_normalize(a) == _normalize(b) for a, b in zip(window, orig_lines)):
            content_lines[i : i + len(orig_lines)] = mod_lines
            return "\n".join(content_lines)

    # Pass 2: allow partial matches — score each window and take the best
    best_idx = -1
    best_score = 0
    threshold = max(0.6, 1.0 - (0.1 * len(orig_lines)))

    norm_orig = [_normalize(l) for l in orig_lines]
    for i in range(len(content_lines) - len(orig_lines) + 1):
        norm_window = [_normalize(l) for l in content_lines[i : i + len(orig_lines)]]
        matches = sum(1 for a, b in zip(norm_window, norm_orig) if a == b)
        score = matches / len(orig_lines)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_score >= threshold and best_idx >= 0:
        content_lines[best_idx : best_idx + len(orig_lines)] = mod_lines
        return "\n".join(content_lines)

    # Pass 3: substring containment — find a window where most orig lines
    # appear as substrings in content lines (handles minor reformatting)
    for i in range(len(content_lines) - len(orig_lines) + 1):
        window = content_lines[i : i + len(orig_lines)]
        matches = 0
        for ol in norm_orig:
            if not ol:
                matches += 1
                continue
            for wl in window:
                if ol in _normalize(wl) or _normalize(wl) in ol:
                    matches += 1
                    break
        if matches >= len(orig_lines) * 0.7:
            content_lines[i : i + len(orig_lines)] = mod_lines
            return "\n".join(content_lines)

    # Pass 4: anchor on a distinctive line, then expand
    for anchor_idx, ol in enumerate(norm_orig):
        if len(ol) < 8:
            continue
        for ci in range(len(content_lines)):
            if _normalize(content_lines[ci]) == ol:
                start = ci - anchor_idx
                end = start + len(orig_lines)
                if start < 0 or end > len(content_lines):
                    continue
                window = content_lines[start:end]
                matches = sum(
                    1
                    for a, b in zip(
                        [_normalize(l) for l in window], norm_orig
                    )
                    if a == b
                )
                if matches >= len(orig_lines) * 0.5:
                    content_lines[start:end] = mod_lines
                    return "\n".join(content_lines)

    return None

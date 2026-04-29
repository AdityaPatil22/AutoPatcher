def _to_str(val) -> str:
    if isinstance(val, list):
        return "\n".join(str(item) for item in val)
    return str(val) if val else ""


def apply_changes(content: str, changes: list[dict]) -> str:
    result = content
    for change in changes:
        original = _to_str(change.get("original", ""))
        modified = _to_str(change.get("modified", ""))
        if not original:
            continue

        if original in result:
            result = result.replace(original, modified, 1)
        else:
            result = _fuzzy_replace(result, original, modified)

    return result


def _fuzzy_replace(content: str, original: str, modified: str) -> str:
    orig_lines = original.strip().split("\n")
    content_lines = content.split("\n")

    for i in range(len(content_lines) - len(orig_lines) + 1):
        window = content_lines[i : i + len(orig_lines)]
        if all(a.strip() == b.strip() for a, b in zip(window, orig_lines)):
            mod_lines = modified.split("\n") if modified else []
            content_lines[i : i + len(orig_lines)] = mod_lines
            return "\n".join(content_lines)

    stripped_orig = [l.strip() for l in orig_lines]
    for i in range(len(content_lines) - len(orig_lines) + 1):
        window = [l.strip() for l in content_lines[i : i + len(orig_lines)]]
        match_count = sum(1 for a, b in zip(window, stripped_orig) if a == b)
        if match_count >= len(orig_lines) * 0.7:
            mod_lines = modified.split("\n") if modified else []
            content_lines[i : i + len(orig_lines)] = mod_lines
            return "\n".join(content_lines)

    return content

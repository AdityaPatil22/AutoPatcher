import difflib


def generate_unified_diff(
    original: str,
    fixed: str,
    filename: str = "file.py",
) -> str:
    """Generate a unified diff between original and fixed code."""
    original_lines = original.splitlines(keepends=True)
    fixed_lines = fixed.splitlines(keepends=True)

    if original_lines and not original_lines[-1].endswith("\n"):
        original_lines[-1] += "\n"
    if fixed_lines and not fixed_lines[-1].endswith("\n"):
        fixed_lines[-1] += "\n"

    diff = difflib.unified_diff(
        original_lines,
        fixed_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm="\n",
    )

    return "".join(diff)

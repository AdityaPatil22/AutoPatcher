"""Shared constants for file discovery and indexing."""

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".swift", ".kt", ".vue", ".svelte",
}

SKIP_DIRS = {
    "node_modules", ".next", "__pycache__", ".git", "dist", "build",
    ".venv", "venv", "env", ".tox", ".mypy_cache", ".pytest_cache",
    "coverage", ".nuxt", ".output", "out", "target", "bin", "obj",
}

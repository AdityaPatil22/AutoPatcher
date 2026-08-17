"""Routes for repository indexing and file tree retrieval."""

import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.config as config
from app.db import get_db
from app.models import IndexRequest
from app.models_db import User
from app.routes.auth import get_current_user
from app.services.indexer import clear_index, get_index_stats, get_indexed_files, index_repository
from app.utils.tree import build_file_tree

logger = logging.getLogger(__name__)

router = APIRouter(tags=["index"])

_GITHUB_URL_RE = re.compile(r"^https://github\.com/[\w.\-]+/[\w.\-]+/?$")


def _remove_user_clone_dir(user_id: int) -> None:
    """Delete all cloned repo files for a user from CLONE_DIR."""
    user_clone_dir = config.CLONE_DIR / str(user_id)
    if user_clone_dir.exists():
        shutil.rmtree(user_clone_dir)


def _clone_github_repo(github_url: str, user: User) -> Path:
    """Clone a GitHub repo (shallow) into a per-user subdirectory of CLONE_DIR.

    Uses the user's OAuth token so private repositories are accessible when the
    token has repo scope.
    """
    url = github_url.rstrip("/")
    if not _GITHUB_URL_RE.match(url):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL. Expected https://github.com/owner/repo")

    parts = url.rstrip("/").split("/")
    owner, repo_name = parts[-2], parts[-1]

    try:
        token = user.get_access_token()
    except Exception:
        raise HTTPException(status_code=401, detail="Could not decrypt access token. Please log in again.")

    # Wipe any previously cloned repo(s) for this user, not just a same-named one.
    _remove_user_clone_dir(user.id)

    user_clone_dir = config.CLONE_DIR / str(user.id)
    user_clone_dir.mkdir(parents=True, exist_ok=True)

    target = user_clone_dir / repo_name
    auth_url = f"https://x-access-token:{token}@github.com/{owner}/{repo_name}.git"

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", auth_url, str(target)],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.CalledProcessError as e:
        logger.error("git clone failed for %s/%s: %s", owner, repo_name, e.stderr)
        if not user.has_repo_scope:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Failed to clone repository. Your GitHub token does not have repo scope. "
                    "Log out and log in again to grant access to private repositories."
                ),
            )
        raise HTTPException(status_code=400, detail=f"Failed to clone repository: {e.stderr.strip()}")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Clone timed out. The repository may be too large.")

    return target


@router.post("/index")
def index_repo(
    req: IndexRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Index a repository from a GitHub URL."""
    repo = _clone_github_repo(req.github_url, user)
    parts = req.github_url.rstrip("/").split("/")
    user.github_repo_owner = parts[-2]
    user.github_repo_name = parts[-1]
    user.repo_path = str(repo)
    db.commit()

    result = index_repository(repo, user.id)
    return {
        "status": "ok",
        "files_indexed": result["files_indexed"],
        "chunks_created": result["chunks_created"],
        "message": f"Indexed {result['files_indexed']} files ({result['chunks_created']} chunks)",
    }


@router.delete("/index")
def delete_index(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear the user's indexed repository from ChromaDB, disk, and reset repo metadata."""
    clear_index(user.id)
    _remove_user_clone_dir(user.id)
    user.repo_path = None
    user.github_repo_owner = None
    user.github_repo_name = None
    db.commit()
    return {"status": "ok", "message": "Index cleared"}


@router.get("/index/status")
def index_status(user: User = Depends(get_current_user)):
    """Return current index stats (whether indexed and chunk count)."""
    return get_index_stats(user.id)


@router.get("/index/files")
def index_files(user: User = Depends(get_current_user)):
    """Return the indexed file tree with relative paths."""
    raw_paths = get_indexed_files(user.id)
    if not raw_paths:
        return {"tree": [], "total_files": 0}

    prefix = os.path.commonpath(raw_paths) if len(raw_paths) > 1 else str(Path(raw_paths[0]).parent)
    prefix = prefix.rstrip("/") + "/"

    relative = [p[len(prefix):] if p.startswith(prefix) else p for p in raw_paths]

    tree = build_file_tree(sorted(relative))
    return {"tree": tree, "total_files": len(raw_paths), "root": prefix}

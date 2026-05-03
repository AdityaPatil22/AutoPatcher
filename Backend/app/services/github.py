"""GitHub API service for branch creation, file commits, and pull request management."""

import base64
import difflib
import hashlib
import re

import httpx

API = "https://api.github.com"
TIMEOUT = 20


class GitHubAPIError(Exception):
    """Raised when a GitHub API call fails."""

    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(message)


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _slugify(text: str, max_len: int = 48) -> str:
    """Turn a ticket title into a branch-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug[:max_len].rstrip("-")


async def get_default_branch(token: str, owner: str, repo: str) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{API}/repos/{owner}/{repo}", headers=_headers(token))
        if resp.status_code == 401:
            raise GitHubAPIError(401, "GitHub token is invalid or expired. Please log in again.")
        if resp.status_code == 403:
            raise GitHubAPIError(403, "Insufficient permissions. Please re-login to grant repo access.")
        if resp.status_code != 200:
            raise GitHubAPIError(resp.status_code, f"Failed to fetch repo info: {resp.text}")
        return resp.json()["default_branch"]


async def get_branch_sha(token: str, owner: str, repo: str, branch: str) -> str:
    """Get the latest commit SHA of a branch."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(
            f"{API}/repos/{owner}/{repo}/git/ref/heads/{branch}",
            headers=_headers(token),
        )
        if resp.status_code != 200:
            raise GitHubAPIError(resp.status_code, f"Branch '{branch}' not found: {resp.text}")
        return resp.json()["object"]["sha"]


async def create_branch(token: str, owner: str, repo: str, branch_name: str, from_sha: str) -> None:
    """Create a new branch from a given commit SHA."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{API}/repos/{owner}/{repo}/git/refs",
            headers=_headers(token),
            json={"ref": f"refs/heads/{branch_name}", "sha": from_sha},
        )
        if resp.status_code == 422:
            raise GitHubAPIError(422, f"Branch '{branch_name}' already exists.")
        if resp.status_code not in (200, 201):
            raise GitHubAPIError(resp.status_code, f"Failed to create branch: {resp.text}")


def _apply_targeted_changes(original_code: str, fixed_code: str, real_content: str) -> str:
    """Apply only the lines that actually changed between original and fixed onto real_content.

    This prevents the PR from showing the entire file as changed when the LLM
    subtly reformats untouched lines (whitespace, line endings, etc.).
    """
    orig_lines = original_code.splitlines()
    fixed_lines = fixed_code.splitlines()
    result_lines = real_content.splitlines()

    matcher = difflib.SequenceMatcher(None, orig_lines, fixed_lines)
    offset = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        old_chunk = orig_lines[i1:i2]
        new_chunk = fixed_lines[j1:j2]
        pos = i1 + offset

        if tag == "replace" and pos + len(old_chunk) <= len(result_lines) and result_lines[pos : pos + len(old_chunk)] == old_chunk:
            result_lines[pos : pos + len(old_chunk)] = new_chunk
            offset += len(new_chunk) - len(old_chunk)
        elif tag == "insert":
            result_lines[pos:pos] = new_chunk
            offset += len(new_chunk)
        elif tag == "delete" and pos + len(old_chunk) <= len(result_lines) and result_lines[pos : pos + len(old_chunk)] == old_chunk:
            del result_lines[pos : pos + len(old_chunk)]
            offset -= len(old_chunk)
        else:
            # Fuzzy search: look near the expected position for the old chunk
            found = False
            search_start = max(0, pos - 10)
            search_end = min(len(result_lines), pos + len(old_chunk) + 10)
            for s in range(search_start, search_end):
                if result_lines[s : s + len(old_chunk)] == old_chunk:
                    result_lines[s : s + len(old_chunk)] = new_chunk
                    offset = (s - i1) + (len(new_chunk) - len(old_chunk))
                    found = True
                    break
            if not found:
                raise GitHubAPIError(
                    409,
                    f"File has diverged from the indexed version — could not apply change at line {i1 + 1}.",
                )

    trailing_newline = real_content.endswith("\n")
    result = "\n".join(result_lines)
    if trailing_newline and not result.endswith("\n"):
        result += "\n"
    return result


async def _fetch_file_content(
    client: httpx.AsyncClient, headers: dict, owner: str, repo: str, path: str, ref: str,
) -> str | None:
    """Fetch a file's decoded content from GitHub. Returns None if not found."""
    resp = await client.get(
        f"{API}/repos/{owner}/{repo}/contents/{path}",
        headers=headers,
        params={"ref": ref},
    )
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise GitHubAPIError(resp.status_code, f"Failed to fetch {path}: {resp.text}")
    data = resp.json()
    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8")
    return data.get("content", "")


async def _resolve_repo_path(
    client: httpx.AsyncClient, headers: dict, owner: str, repo: str,
    tree_sha: str, raw_path: str,
) -> str:
    """Convert a local absolute/messy path into the correct repo-relative path.

    Strategy:
      1. Strip known clone-dir prefixes to get a repo-relative candidate.
      2. If the candidate looks good (no absolute prefix), try it directly.
      3. Otherwise, fetch the full repo tree and find the file by name.
    """
    from app.config import CLONE_DIR

    candidate = raw_path

    # Strip absolute clone-dir prefix:
    #   /tmp/autopatch_clones/1/RepoName/components/Foo.vue -> components/Foo.vue
    clone_prefix = str(CLONE_DIR)
    if candidate.startswith(clone_prefix):
        candidate = candidate[len(clone_prefix):]
        candidate = candidate.lstrip("/")
        # Remove "<user_id>/<repo_name>/" prefix (first two segments)
        parts = candidate.split("/", 2)
        if len(parts) > 2:
            candidate = parts[2]
        elif len(parts) == 2:
            candidate = parts[1]

    # Also handle generic /tmp/ or other absolute paths
    if candidate.startswith("/"):
        # Try to find repo name in path and strip everything before it
        segments = candidate.strip("/").split("/")
        repo_lower = repo.lower()
        for i, seg in enumerate(segments):
            if seg.lower() == repo_lower and i + 1 < len(segments):
                candidate = "/".join(segments[i + 1 :])
                break
        else:
            candidate = segments[-1]

    # Quick check: does this path exist?
    check = await _fetch_file_content(client, headers, owner, repo, candidate, tree_sha)
    if check is not None:
        return candidate

    # Fallback: search the repo tree for a matching filename
    filename = candidate.rsplit("/", 1)[-1]
    tree_resp = await client.get(
        f"{API}/repos/{owner}/{repo}/git/trees/{tree_sha}",
        headers=headers,
        params={"recursive": "1"},
    )
    if tree_resp.status_code == 200:
        for item in tree_resp.json().get("tree", []):
            if item["type"] == "blob" and item["path"].endswith(f"/{filename}"):
                return item["path"]
            if item["type"] == "blob" and item["path"] == filename:
                return item["path"]

    return candidate


async def commit_patches(
    token: str,
    owner: str,
    repo: str,
    branch: str,
    patches: list[dict],
    commit_message: str,
) -> str:
    """Commit all patched files to the branch using the Git Trees API (single atomic commit).

    For each file, fetches the current content from GitHub and applies only the
    lines that actually changed, so the PR diff stays minimal.
    """
    headers = _headers(token)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        ref_resp = await client.get(
            f"{API}/repos/{owner}/{repo}/git/ref/heads/{branch}",
            headers=headers,
        )
        if ref_resp.status_code != 200:
            raise GitHubAPIError(ref_resp.status_code, f"Could not read branch ref: {ref_resp.text}")
        base_sha = ref_resp.json()["object"]["sha"]

        commit_resp = await client.get(
            f"{API}/repos/{owner}/{repo}/git/commits/{base_sha}",
            headers=headers,
        )
        if commit_resp.status_code != 200:
            raise GitHubAPIError(commit_resp.status_code, f"Could not read base commit: {commit_resp.text}")
        base_tree_sha = commit_resp.json()["tree"]["sha"]

        tree_items = []
        for patch in patches:
            resolved_path = await _resolve_repo_path(
                client, headers, owner, repo, base_sha, patch["file_path"],
            )

            real_content = await _fetch_file_content(
                client, headers, owner, repo, resolved_path, branch,
            )

            if real_content is not None:
                final_content = _apply_targeted_changes(
                    patch["original_code"], patch["fixed_code"], real_content,
                )
            else:
                final_content = patch["fixed_code"]

            blob_resp = await client.post(
                f"{API}/repos/{owner}/{repo}/git/blobs",
                headers=headers,
                json={"content": final_content, "encoding": "utf-8"},
            )
            if blob_resp.status_code != 201:
                raise GitHubAPIError(blob_resp.status_code, f"Failed to create blob for {resolved_path}: {blob_resp.text}")
            tree_items.append({
                "path": resolved_path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_resp.json()["sha"],
            })

        tree_resp = await client.post(
            f"{API}/repos/{owner}/{repo}/git/trees",
            headers=headers,
            json={"base_tree": base_tree_sha, "tree": tree_items},
        )
        if tree_resp.status_code != 201:
            raise GitHubAPIError(tree_resp.status_code, f"Failed to create tree: {tree_resp.text}")
        new_tree_sha = tree_resp.json()["sha"]

        new_commit_resp = await client.post(
            f"{API}/repos/{owner}/{repo}/git/commits",
            headers=headers,
            json={
                "message": commit_message,
                "tree": new_tree_sha,
                "parents": [base_sha],
            },
        )
        if new_commit_resp.status_code != 201:
            raise GitHubAPIError(new_commit_resp.status_code, f"Failed to create commit: {new_commit_resp.text}")
        new_commit_sha = new_commit_resp.json()["sha"]

        update_ref_resp = await client.patch(
            f"{API}/repos/{owner}/{repo}/git/refs/heads/{branch}",
            headers=headers,
            json={"sha": new_commit_sha},
        )
        if update_ref_resp.status_code != 200:
            raise GitHubAPIError(update_ref_resp.status_code, f"Failed to update branch ref: {update_ref_resp.text}")

        return new_commit_sha


async def create_pull_request(
    token: str,
    owner: str,
    repo: str,
    head: str,
    base: str,
    title: str,
    body: str,
) -> dict:
    """Create a pull request and return {url, number, html_url}."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{API}/repos/{owner}/{repo}/pulls",
            headers=_headers(token),
            json={"title": title, "body": body, "head": head, "base": base},
        )
        if resp.status_code not in (200, 201):
            raise GitHubAPIError(resp.status_code, f"Failed to create pull request: {resp.text}")
        data = resp.json()
        return {
            "pr_number": data["number"],
            "pr_url": data["html_url"],
        }


def make_branch_name(ticket_title: str) -> str:
    """Generate a deterministic but unique-ish branch name from a ticket title."""
    slug = _slugify(ticket_title)
    short_hash = hashlib.sha1(ticket_title.encode()).hexdigest()[:7]
    return f"autopatch/{slug}-{short_hash}"

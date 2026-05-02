import type { IndexFiles, IndexResult, IndexStatus } from "../types";
import { request } from "./client";

export function getIndexStatus() {
  return request<IndexStatus>("/index/status");
}

export function indexRepository(repoPath?: string, githubUrl?: string) {
  const body: Record<string, string> = {};
  if (repoPath) body.repo_path = repoPath;
  if (githubUrl) body.github_url = githubUrl;
  return request<IndexResult>("/index", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getIndexFiles() {
  return request<IndexFiles>("/index/files");
}

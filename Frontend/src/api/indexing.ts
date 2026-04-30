import type { IndexFiles, IndexResult, IndexStatus } from "../types";
import { request } from "./client";

export function getIndexStatus() {
  return request<IndexStatus>("/index/status");
}

export function indexRepository(repoPath?: string) {
  return request<IndexResult>("/index", {
    method: "POST",
    body: JSON.stringify(repoPath ? { repo_path: repoPath } : {}),
  });
}

export function getIndexFiles() {
  return request<IndexFiles>("/index/files");
}

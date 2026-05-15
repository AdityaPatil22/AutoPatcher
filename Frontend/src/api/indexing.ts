import type { IndexFiles, IndexResult, IndexStatus } from "../types";
import { request } from "./client";

export function getIndexStatus() {
  return request<IndexStatus>("/index/status");
}

export function indexRepository(githubUrl: string) {
  return request<IndexResult>("/index", {
    method: "POST",
    body: JSON.stringify({ github_url: githubUrl }),
  });
}

export function getIndexFiles() {
  return request<IndexFiles>("/index/files");
}

export function clearIndex() {
  return request<{ status: string; message: string }>("/index", {
    method: "DELETE",
  });
}

import type {
  CloudService,
  IndexResult,
  IndexStatus,
  LLMProvider,
  PatchOutput,
  RefineInput,
  SearchMode,
  Settings,
  TicketInput,
} from "./types";

const API_BASE = "/api";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      body.detail || `API error (${res.status})`
    );
  }

  return res.json();
}

export function generateFix(ticket: TicketInput) {
  return request<PatchOutput>("/generate-fix", {
    method: "POST",
    body: JSON.stringify(ticket),
  });
}

export function refineFix(input: RefineInput) {
  return request<PatchOutput>("/refine-fix", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getIndexStatus() {
  return request<IndexStatus>("/index/status");
}

export function indexRepository(repoPath?: string) {
  return request<IndexResult>("/index", {
    method: "POST",
    body: JSON.stringify(repoPath ? { repo_path: repoPath } : {}),
  });
}

export function getSettings() {
  return request<Settings>("/settings");
}

export function setProvider(provider: LLMProvider) {
  return request<{ provider: LLMProvider }>("/settings/provider", {
    method: "PUT",
    body: JSON.stringify({ provider }),
  });
}

export function setModel(model: string) {
  return request<{ model: string }>("/settings/model", {
    method: "PUT",
    body: JSON.stringify({ model }),
  });
}

export function setApiKey(service: CloudService, apiKey: string) {
  return request<{ service: string; key_hint: string }>("/settings/api-key", {
    method: "PUT",
    body: JSON.stringify({ service, api_key: apiKey }),
  });
}

export function setSearchMode(mode: SearchMode) {
  return request<{ search_mode: SearchMode }>("/settings/search-mode", {
    method: "PUT",
    body: JSON.stringify({ mode }),
  });
}

export function setMaxContextFiles(maxFiles: number) {
  return request<{ max_context_files: number }>("/settings/max-context-files", {
    method: "PUT",
    body: JSON.stringify({ max_files: maxFiles }),
  });
}

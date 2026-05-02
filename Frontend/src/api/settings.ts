import type { LLMProvider, Settings } from "../types";
import { request } from "./client";

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

export function setMaxContextFiles(maxFiles: number) {
  return request<{ max_context_files: number }>("/settings/max-context-files", {
    method: "PUT",
    body: JSON.stringify({ max_files: maxFiles }),
  });
}

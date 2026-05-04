import type {
  BuildPatchesRequest,
  CreatePRRequest,
  CreatePRResponse,
  PatchOutput,
  PromptOutput,
  RefineInput,
  TicketInput,
} from "../types";
import { request } from "./client";

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

export function createPR(input: CreatePRRequest) {
  return request<CreatePRResponse>("/create-pr", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function generatePrompt(ticket: TicketInput) {
  return request<PromptOutput>("/generate-prompt", {
    method: "POST",
    body: JSON.stringify(ticket),
  });
}

export function refinePrompt(input: RefineInput) {
  return request<PromptOutput>("/refine-prompt", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function buildPatches(input: BuildPatchesRequest) {
  return request<PatchOutput>("/build-patches", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

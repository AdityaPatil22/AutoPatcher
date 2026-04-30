import type { PatchOutput, RefineInput, TicketInput } from "../types";
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

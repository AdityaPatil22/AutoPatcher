import type { User } from "../types";
import { request } from "./client";

export function getMe() {
  return request<User>("/auth/me");
}

export function logout() {
  return request<{ status: string }>("/auth/logout", { method: "POST" });
}

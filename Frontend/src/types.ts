export interface FilePatch {
  file_path: string;
  original_code: string;
  fixed_code: string;
  diff: string;
  warning: string;
}

export interface PatchOutput {
  ticket_title: string;
  patches: FilePatch[];
  explanation: string;
}

export interface TicketInput {
  title: string;
  description: string;
  file_hint?: string;
}

export interface RefineInput {
  title: string;
  description: string;
  feedback: string;
  file_hint?: string;
  previous_patches: FilePatch[];
}

export interface User {
  github_id: number;
  username: string;
  email: string | null;
  avatar_url: string;
}

export type LLMProvider = "local" | "gemini";

export interface Settings {
  provider: LLMProvider;
  model: string;
  gemini_available: boolean;
  max_context_files: number;
  repo_path: string | null;
}

export interface IndexStatus {
  indexed: boolean;
  total_chunks: number;
}

export interface FileNode {
  name: string;
  type: "file" | "folder";
  children?: FileNode[];
}

export interface IndexFiles {
  tree: FileNode[];
  total_files: number;
  root?: string;
}

export interface IndexResult {
  status: string;
  files_indexed: number;
  chunks_created: number;
  message?: string;
}

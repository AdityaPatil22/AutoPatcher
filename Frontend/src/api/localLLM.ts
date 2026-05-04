const OLLAMA_BASE = "http://localhost:11434";

export interface OllamaChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

interface OllamaChatResponse {
  message: { role: string; content: string };
  done: boolean;
}

/**
 * Call the local Ollama instance using the /api/chat endpoint.
 * Uses `stream: false` so we get a single JSON response.
 */
export async function callLocalLLM(
  messages: OllamaChatMessage[],
  model: string = "llama3"
): Promise<string> {
  const res = await fetch(`${OLLAMA_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, messages, stream: false }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `Ollama returned ${res.status}. ${text || "Is the model pulled?"}`
    );
  }

  const data: OllamaChatResponse = await res.json();
  return data.message?.content ?? "";
}

/**
 * Quick health check — resolves true if Ollama is reachable.
 */
export async function isOllamaRunning(): Promise<boolean> {
  try {
    const res = await fetch(OLLAMA_BASE, { signal: AbortSignal.timeout(2000) });
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * List models currently available in the local Ollama instance.
 */
export async function listOllamaModels(): Promise<string[]> {
  try {
    const res = await fetch(`${OLLAMA_BASE}/api/tags`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) return [];
    const data = await res.json();
    return (data.models ?? []).map((m: { name: string }) => m.name);
  } catch {
    return [];
  }
}

import { useRef, useState } from "react";
import {
  buildPatches,
  generateFix,
  generatePrompt,
  refineFix,
  refinePrompt,
} from "../api/patches";
import { callLocalLLM, isOllamaRunning, type OllamaChatMessage } from "../api/localLLM";
import type { LLMProvider, PatchOutput, TicketInput } from "../types";

interface PatchGenOptions {
  llmProvider: LLMProvider;
  modelName: string;
  onLlmRequest?: () => void;
}

export function usePatchGeneration({ llmProvider, modelName, onLlmRequest }: PatchGenOptions) {
  const [ticket, setTicket] = useState<TicketInput>({
    title: "",
    description: "",
  });
  const [fileHint, setFileHint] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [refineLoading, setRefineLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<PatchOutput | null>(null);
  const [feedback, setFeedback] = useState("");
  const [showRawJson, setShowRawJson] = useState(false);

  const loadingTimers = useRef<ReturnType<typeof setTimeout>[]>([]);

  function clearLoadingTimers() {
    loadingTimers.current.forEach(clearTimeout);
    loadingTimers.current = [];
  }

  async function handleGenerateFix(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!ticket.title.trim() || !ticket.description.trim()) return;

    setLoading(true);
    setLoadingStep(0);
    setError("");
    setResult(null);
    setFeedback("");
    setShowRawJson(false);

    clearLoadingTimers();
    loadingTimers.current.push(setTimeout(() => setLoadingStep(1), 2000));
    loadingTimers.current.push(setTimeout(() => setLoadingStep(2), 5000));

    try {
      const payload: TicketInput = {
        title: ticket.title,
        description: ticket.description,
      };
      if (fileHint.trim()) payload.file_hint = fileHint;

      let data: PatchOutput;

      if (llmProvider === "local-ollama") {
        data = await _browserLocalGenerate(payload);
      } else {
        data = await generateFix(payload);
        onLlmRequest?.();
      }

      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      clearLoadingTimers();
      setLoading(false);
      setLoadingStep(0);
    }
  }

  async function _browserLocalGenerate(payload: TicketInput): Promise<PatchOutput> {
    const running = await isOllamaRunning();
    if (!running) {
      throw new Error(
        "Ollama is not running. Please install and run Ollama locally to use this feature."
      );
    }

    setLoadingStep(1);
    const promptData = await generatePrompt(payload);

    setLoadingStep(2);
    const messages = promptData.messages.map((m) => ({
      role: m.role as OllamaChatMessage["role"],
      content: m.content,
    }));
    const model = modelName.trim() || promptData.model_hint;
    const rawResponse = await callLocalLLM(messages, model);

    if (!rawResponse.trim()) {
      throw new Error("Local LLM returned an empty response. Try a different model.");
    }

    return buildPatches({
      session_id: promptData.session_id,
      raw_response: rawResponse,
    });
  }

  async function handleRefineFix() {
    if (!feedback.trim() || !result) return;

    setRefineLoading(true);
    setError("");

    try {
      const refineInput = {
        title: ticket.title,
        description: ticket.description,
        feedback,
        file_hint: fileHint.trim() || undefined,
        previous_patches: result.patches,
      };

      let data: PatchOutput;

      if (llmProvider === "local-ollama") {
        data = await _browserLocalRefine(refineInput);
      } else {
        data = await refineFix(refineInput);
        onLlmRequest?.();
      }

      setResult(data);
      setFeedback("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setRefineLoading(false);
    }
  }

  async function _browserLocalRefine(
    refineInput: Parameters<typeof refineFix>[0]
  ): Promise<PatchOutput> {
    const running = await isOllamaRunning();
    if (!running) {
      throw new Error(
        "Ollama is not running. Please install and run Ollama locally to use this feature."
      );
    }

    const promptData = await refinePrompt(refineInput);

    const messages = promptData.messages.map((m) => ({
      role: m.role as OllamaChatMessage["role"],
      content: m.content,
    }));
    const model = modelName.trim() || promptData.model_hint;
    const rawResponse = await callLocalLLM(messages, model);

    if (!rawResponse.trim()) {
      throw new Error("Local LLM returned an empty response. Try a different model.");
    }

    return buildPatches({
      session_id: promptData.session_id,
      raw_response: rawResponse,
    });
  }

  return {
    ticket,
    setTicket,
    fileHint,
    setFileHint,
    loading,
    loadingStep,
    refineLoading,
    error,
    setError,
    result,
    feedback,
    setFeedback,
    showRawJson,
    setShowRawJson,
    handleGenerateFix,
    handleRefineFix,
  } as const;
}

export type UsePatchGenerationReturn = ReturnType<typeof usePatchGeneration>;

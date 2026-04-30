import { useRef, useState } from "react";
import { generateFix, refineFix } from "../api/patches";
import type { PatchOutput, TicketInput } from "../types";

export function usePatchGeneration() {
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

      const data = await generateFix(payload);
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      clearLoadingTimers();
      setLoading(false);
      setLoadingStep(0);
    }
  }

  async function handleRefineFix() {
    if (!feedback.trim() || !result) return;

    setRefineLoading(true);
    setError("");

    try {
      const data = await refineFix({
        title: ticket.title,
        description: ticket.description,
        feedback,
        file_hint: fileHint.trim() || undefined,
        previous_patches: result.patches,
      });
      setResult(data);
      setFeedback("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setRefineLoading(false);
    }
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

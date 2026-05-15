import { useCallback, useRef, useState } from "react";
import {
  getSettings,
  setMaxContextFiles,
  setModel,
  setProvider,
} from "../api/settings";
import type { LLMProvider } from "../types";

export function useSettings() {
  const [llmProvider, setLlmProvider] = useState<LLMProvider>("browser");
  const [modelName, setModelName] = useState("");
  const [maxContextFiles, setMaxContextFilesState] = useState(3);
  const [repoName, setRepoName] = useState<string | null>(null);
  const [geminiRequestsRemaining, setGeminiRequestsRemaining] = useState(5);
  const [geminiModel, setGeminiModel] = useState("");
  const [geminiDailyLimit, setGeminiDailyLimit] = useState(5);

  const modelDebounce = useRef<ReturnType<typeof setTimeout>>(undefined);

  const fetchSettings = useCallback(async () => {
    try {
      const s = await getSettings();
      setMaxContextFilesState(s.max_context_files);
      setLlmProvider(s.provider);
      setModelName(s.model);
      setGeminiModel(s.gemini_model);
      setGeminiRequestsRemaining(s.gemini_requests_remaining);
      setGeminiDailyLimit(s.gemini_daily_limit);
      if (s.repo_path) {
        const parts = s.repo_path.replace(/\/+$/, "").split("/");
        setRepoName(parts[parts.length - 1] || null);
      } else {
        setRepoName(null);
      }
    } catch {
      /* backend not reachable */
    }
  }, []);

  async function handleProviderChange(provider: LLMProvider) {
    setLlmProvider(provider);
    const restoredModel = provider === "gemini" ? geminiModel : "";
    setModelName(restoredModel);
    try {
      await Promise.all([setProvider(provider), setModel(restoredModel)]);
    } catch {
      await fetchSettings();
    }
  }

  function handleModelInput(value: string) {
    setModelName(value);
    clearTimeout(modelDebounce.current);
    modelDebounce.current = setTimeout(async () => {
      if (value.trim()) {
        try {
          await setModel(value.trim());
        } catch {
          /* ignore */
        }
      }
    }, 600);
  }

  async function handleMaxContextFilesChange(value: number) {
    if (value < 1 || value > 20) return;
    setMaxContextFilesState(value);
    try {
      await setMaxContextFiles(value);
    } catch {
      await fetchSettings();
    }
  }

  return {
    llmProvider,
    modelName,
    geminiModel,
    maxContextFiles,
    repoName,
    geminiRequestsRemaining,
    geminiDailyLimit,
    fetchSettings,
    handleProviderChange,
    handleModelInput,
    handleMaxContextFilesChange,
  } as const;
}

export type UseSettingsReturn = ReturnType<typeof useSettings>;

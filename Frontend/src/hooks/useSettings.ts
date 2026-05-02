import { useCallback, useRef, useState } from "react";
import {
  getSettings,
  setMaxContextFiles,
  setModel,
  setProvider,
} from "../api/settings";
import type { LLMProvider } from "../types";

export function useSettings() {
  const [llmProvider, setLlmProvider] = useState<LLMProvider>("local");
  const [modelName, setModelName] = useState("");
  const [maxContextFiles, setMaxContextFilesState] = useState(3);

  const modelDebounce = useRef<ReturnType<typeof setTimeout>>(undefined);

  const fetchSettings = useCallback(async () => {
    try {
      const s = await getSettings();
      setMaxContextFilesState(s.max_context_files);
      setLlmProvider(s.provider);
      setModelName(s.model);
    } catch {
      /* backend not reachable */
    }
  }, []);

  async function handleProviderChange(provider: LLMProvider) {
    setLlmProvider(provider);
    try {
      await setProvider(provider);
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
    maxContextFiles,
    fetchSettings,
    handleProviderChange,
    handleModelInput,
    handleMaxContextFilesChange,
  } as const;
}

export type UseSettingsReturn = ReturnType<typeof useSettings>;

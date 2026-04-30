import { useCallback, useRef, useState } from "react";
import {
  getSettings,
  setApiKey,
  setMaxContextFiles,
  setModel,
  setProvider,
  setSearchMode,
} from "../api/settings";
import type { CloudService, LLMProvider, SearchMode } from "../types";

export function useSettings() {
  const [llmProvider, setLlmProvider] = useState<LLMProvider>("local");
  const [modelName, setModelName] = useState("");
  const [cloudService, setCloudService] = useState<CloudService>("openai");
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [openaiKeyHint, setOpenaiKeyHint] = useState("");
  const [geminiKeyHint, setGeminiKeyHint] = useState("");
  const [keySaved, setKeySaved] = useState(false);
  const [searchMode, setSearchModeState] = useState<SearchMode>("hybrid");
  const [maxContextFiles, setMaxContextFilesState] = useState(3);

  const modelDebounce = useRef<ReturnType<typeof setTimeout>>(undefined);

  const fetchSettings = useCallback(async () => {
    try {
      const s = await getSettings();
      setSearchModeState(s.search_mode);
      setMaxContextFilesState(s.max_context_files);
      setLlmProvider(s.provider);
      setModelName(s.model);
      setOpenaiKeyHint(s.openai_key_hint);
      setGeminiKeyHint(s.gemini_key_hint);
      if (s.cloud_backend) {
        setCloudService(s.cloud_backend);
      }
    } catch {
      /* backend not reachable */
    }
  }, []);

  async function handleProviderChange(provider: LLMProvider) {
    setLlmProvider(provider);
    setApiKeyInput("");
    setKeySaved(false);
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

  async function handleSaveApiKey() {
    if (!apiKeyInput.trim()) return;
    try {
      const res = await setApiKey(cloudService, apiKeyInput.trim());
      if (cloudService === "openai") {
        setOpenaiKeyHint(res.key_hint);
      } else {
        setGeminiKeyHint(res.key_hint);
      }
      setApiKeyInput("");
      setKeySaved(true);
      setTimeout(() => setKeySaved(false), 3000);
    } catch {
      /* ignore */
    }
  }

  function handleCloudServiceChange(service: CloudService) {
    setCloudService(service);
    setApiKeyInput("");
    setKeySaved(false);
  }

  async function handleSearchModeChange(mode: SearchMode) {
    setSearchModeState(mode);
    try {
      await setSearchMode(mode);
    } catch {
      await fetchSettings();
    }
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

  const currentKeyHint =
    cloudService === "openai" ? openaiKeyHint : geminiKeyHint;

  return {
    llmProvider,
    modelName,
    cloudService,
    apiKeyInput,
    setApiKeyInput,
    currentKeyHint,
    keySaved,
    searchMode,
    maxContextFiles,
    fetchSettings,
    handleProviderChange,
    handleModelInput,
    handleSaveApiKey,
    handleCloudServiceChange,
    handleSearchModeChange,
    handleMaxContextFilesChange,
  } as const;
}

export type UseSettingsReturn = ReturnType<typeof useSettings>;

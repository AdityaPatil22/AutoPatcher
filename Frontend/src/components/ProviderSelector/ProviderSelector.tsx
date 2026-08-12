import type { LLMProvider } from "../../types";
import OllamaStatus from "../OllamaStatus/OllamaStatus";
import "./ProviderSelector.css";

const PROVIDERS: { value: LLMProvider; label: string; title: string }[] = [
  { value: "local-ollama", label: "Local (Ollama)", title: "Run LLM on your machine via Ollama" },
  { value: "gemini", label: "Gemini", title: "Google Gemini API" },
  { value: "openai", label: "OpenAI", title: "OpenAI API (GPT)" },
  { value: "nvidia", label: "NVIDIA", title: "NVIDIA NIM API" },
];

interface ProviderSelectorProps {
  provider: LLMProvider;
  onChange: (p: LLMProvider) => void;
  modelName: string;
  onModelChange: (model: string) => void;
  llmRequestsRemaining: number;
  llmDailyLimit: number;
  isLoggedIn: boolean;
}

export default function ProviderSelector({
  provider,
  onChange,
  modelName,
  onModelChange,
  llmRequestsRemaining,
  llmDailyLimit,
  isLoggedIn,
}: ProviderSelectorProps) {
  const isCloudProvider = provider !== "local-ollama";

  return (
    <>
      <div className="form-group">
        <label>LLM Provider</label>
        <div className="search-mode-toggle">
          {PROVIDERS.map((p) => (
            <button
              key={p.value}
              type="button"
              className={`mode-btn ${provider === p.value ? "active" : ""}`}
              onClick={() => onChange(p.value)}
              title={p.title}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {provider === "local-ollama" && (
        <OllamaStatus modelName={modelName} onModelChange={onModelChange} />
      )}

      {isCloudProvider && (
        <>
          {isLoggedIn && (
            <div className={`llm-quota ${llmRequestsRemaining === 0 ? "llm-quota-exhausted" : ""}`}>
              <span className="llm-quota-count">{llmRequestsRemaining}/{llmDailyLimit}</span>
              <span> requests remaining today</span>
            </div>
          )}
          <div className="form-group">
            <label>Model</label>
            <input
              type="text"
              value={modelName}
              onChange={(e) => onModelChange(e.target.value)}
              placeholder="e.g. gemini-2.5-flash, gpt-4o, nvidia/nemotron-3.5-lightning-30b-a3b"
            />
          </div>
        </>
      )}
    </>
  );
}

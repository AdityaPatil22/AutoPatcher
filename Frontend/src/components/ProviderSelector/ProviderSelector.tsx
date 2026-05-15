import type { LLMProvider } from "../../types";
import OllamaStatus from "../OllamaStatus/OllamaStatus";
import "./ProviderSelector.css";

interface ProviderSelectorProps {
  provider: LLMProvider;
  onChange: (p: LLMProvider) => void;
  modelName: string;
  onModelChange: (model: string) => void;
  geminiRemaining: number;
  geminiLimit: number;
  geminiModel: string;
}

export default function ProviderSelector({
  provider,
  onChange,
  modelName,
  onModelChange,
  geminiRemaining,
  geminiLimit,
  geminiModel,
}: ProviderSelectorProps) {
  return (
    <>
      <div className="form-group">
        <label>LLM Provider</label>
        <div className="search-mode-toggle">
          <button
            type="button"
            className={`mode-btn ${provider === "browser" ? "active" : ""}`}
            onClick={() => onChange("browser")}
            title="Run LLM on your machine via Ollama"
          >
            Local (Ollama)
          </button>
          <button
            type="button"
            className={`mode-btn ${provider === "gemini" ? "active" : ""}`}
            onClick={() => onChange("gemini")}
          >
            Gemini
          </button>
        </div>
      </div>

      {provider === "browser" && (
        <OllamaStatus modelName={modelName} onModelChange={onModelChange} />
      )}

      {provider === "gemini" && (
        <>
          <div className={`gemini-quota ${geminiRemaining === 0 ? "gemini-quota-exhausted" : ""}`}>
            <span className="gemini-quota-count">{geminiRemaining}/{geminiLimit}</span>
            <span> requests remaining today</span>
          </div>
          <div className="form-group">
            <label>Model</label>
            <div className="gemini-model-badge">{geminiModel || "gemini"}</div>
          </div>
        </>
      )}
    </>
  );
}

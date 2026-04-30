import type { UseSettingsReturn } from "../../hooks/useSettings";
import type { UsePatchGenerationReturn } from "../../hooks/usePatchGeneration";
import "./InputPanel.css";

interface InputPanelProps {
  settings: UseSettingsReturn;
  patchGen: UsePatchGenerationReturn;
}

export default function InputPanel({ settings, patchGen }: InputPanelProps) {
  const {
    llmProvider,
    modelName,
    cloudService,
    apiKeyInput,
    setApiKeyInput,
    currentKeyHint,
    keySaved,
    searchMode,
    maxContextFiles,
    handleProviderChange,
    handleModelInput,
    handleSaveApiKey,
    handleCloudServiceChange,
    handleSearchModeChange,
    handleMaxContextFilesChange,
  } = settings;

  const {
    ticket,
    setTicket,
    fileHint,
    setFileHint,
    loading,
    refineLoading,
    result,
    feedback,
    setFeedback,
    handleGenerateFix,
    handleRefineFix,
  } = patchGen;

  return (
    <section className="panel input-panel">
      <h2>Add Bug Details</h2>
      <form onSubmit={handleGenerateFix}>
        <div className="form-group">
          <label htmlFor="title">Title</label>
          <input
            id="title"
            value={ticket.title}
            onChange={(e) =>
              setTicket((t) => ({ ...t, title: e.target.value }))
            }
            placeholder="e.g. Fix export button issue"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            value={ticket.description}
            onChange={(e) =>
              setTicket((t) => ({ ...t, description: e.target.value }))
            }
            rows={6}
            placeholder="Describe the bug in detail..."
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="fileHint">
            File Hint <span className="optional">(optional)</span>
          </label>
          <input
            id="fileHint"
            value={fileHint}
            onChange={(e) => setFileHint(e.target.value)}
            placeholder="e.g. user_service.py"
          />
        </div>

        <div className="settings-divider">
          <span>Settings</span>
        </div>

        <div className="form-group">
          <label>LLM Provider</label>
          <div className="search-mode-toggle">
            <button
              type="button"
              className={`mode-btn ${llmProvider === "local" ? "active" : ""}`}
              onClick={() => handleProviderChange("local")}
            >
              Local
            </button>
            <button
              type="button"
              className={`mode-btn ${llmProvider === "cloud" ? "active" : ""}`}
              onClick={() => handleProviderChange("cloud")}
            >
              Cloud
            </button>
          </div>
        </div>

        {llmProvider === "local" && (
          <div className="form-group">
            <label htmlFor="modelName">Model Name</label>
            <input
              id="modelName"
              value={modelName}
              onChange={(e) => handleModelInput(e.target.value)}
              placeholder="e.g. llama3:8b, deepseek-coder:6.7b"
            />
          </div>
        )}

        {llmProvider === "cloud" && (
          <>
            <div className="form-group">
              <label>Cloud Service</label>
              <div className="search-mode-toggle">
                <button
                  type="button"
                  className={`mode-btn ${cloudService === "openai" ? "active" : ""}`}
                  onClick={() => handleCloudServiceChange("openai")}
                >
                  OpenAI
                </button>
                <button
                  type="button"
                  className={`mode-btn ${cloudService === "gemini" ? "active" : ""}`}
                  onClick={() => handleCloudServiceChange("gemini")}
                >
                  Gemini
                </button>
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="apiKey">
                API Key
                {currentKeyHint && (
                  <span className="key-hint"> ({currentKeyHint})</span>
                )}
              </label>
              <div className="api-key-row">
                <input
                  id="apiKey"
                  type="password"
                  value={apiKeyInput}
                  onChange={(e) => {
                    setApiKeyInput(e.target.value);
                  }}
                  placeholder={
                    currentKeyHint
                      ? `Current: ${currentKeyHint}`
                      : cloudService === "openai"
                        ? "sk-..."
                        : "AI..."
                  }
                />
                <button
                  type="button"
                  className={`btn btn-save ${keySaved ? "saved" : ""}`}
                  onClick={handleSaveApiKey}
                  disabled={!apiKeyInput.trim() || keySaved}
                >
                  {keySaved ? "Saved" : "Save"}
                </button>
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="cloudModel">
                Model Name <span className="optional">(optional)</span>
              </label>
              <input
                id="cloudModel"
                value={modelName}
                onChange={(e) => handleModelInput(e.target.value)}
                placeholder={
                  cloudService === "openai"
                    ? "default: gpt-4o-mini"
                    : "default: gemini-1.5-flash"
                }
              />
            </div>
          </>
        )}

        <div className="form-group">
          <label>Search Mode</label>
          <div className="search-mode-toggle">
            {(["keyword", "semantic", "hybrid"] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                className={`mode-btn ${searchMode === mode ? "active" : ""}`}
                onClick={() => handleSearchModeChange(mode)}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </button>
            ))}
          </div>
        </div>
        <div className="form-group">
          <label htmlFor="maxFiles">
            Max Context Files
            <span className="optional"> (1-20)</span>
          </label>
          <div className="stepper">
            <button
              type="button"
              className="stepper-btn"
              onClick={() =>
                handleMaxContextFilesChange(maxContextFiles - 1)
              }
              disabled={maxContextFiles <= 1}
            >
              -
            </button>
            <input
              id="maxFiles"
              type="number"
              className="stepper-input"
              value={maxContextFiles}
              min={1}
              max={20}
              onChange={(e) => {
                const v = parseInt(e.target.value, 10);
                if (!isNaN(v)) handleMaxContextFilesChange(v);
              }}
            />
            <button
              type="button"
              className="stepper-btn"
              onClick={() =>
                handleMaxContextFilesChange(maxContextFiles + 1)
              }
              disabled={maxContextFiles >= 20}
            >
              +
            </button>
          </div>
        </div>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
        >
          {loading && <span className="spinner-inline" />}
          {loading ? "Generating..." : "Generate Fix"}
        </button>
      </form>

      {result && (
        <div className="refine-section">
          <h3>Refine Fix</h3>
          <p className="refine-hint">
            Not satisfied? Provide feedback and regenerate.
          </p>
          <div className="form-group">
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={3}
              placeholder="e.g. The fix should also handle the edge case where..."
            />
          </div>
          <button
            className="btn btn-secondary btn-full"
            onClick={handleRefineFix}
            disabled={refineLoading || !feedback.trim()}
            type="button"
          >
            {refineLoading && <span className="spinner-inline" />}
            {refineLoading ? "Refining..." : "Refine Fix"}
          </button>
        </div>
      )}
    </section>
  );
}

import type { UseSettingsReturn } from "../../hooks/useSettings";
import type { UsePatchGenerationReturn } from "../../hooks/usePatchGeneration";
import "./InputPanel.css";

interface InputPanelProps {
  settings: UseSettingsReturn;
  patchGen: UsePatchGenerationReturn;
  isLoggedIn: boolean;
  isIndexed: boolean;
  onLogin: () => void;
  onOpenIndexModal: () => void;
}

export default function InputPanel({
  settings,
  patchGen,
  isLoggedIn,
  isIndexed,
  onLogin,
  onOpenIndexModal,
}: InputPanelProps) {
  const {
    llmProvider,
    modelName,
    maxContextFiles,
    repoName,
    handleProviderChange,
    handleModelInput,
    handleMaxContextFilesChange,
  } = settings;

  const {
    ticket,
    setTicket,
    fileHint,
    setFileHint,
    loading,
    handleGenerateFix,
  } = patchGen;

  const canGenerate = isLoggedIn && isIndexed && !loading;

  return (
    <section className="panel input-panel">
      <h2>Bug Details</h2>
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
              className={`mode-btn ${llmProvider === "gemini" ? "active" : ""}`}
              onClick={() => handleProviderChange("gemini")}
            >
              Gemini
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

        {llmProvider === "gemini" && (
          <div className="form-group">
            <label htmlFor="geminiModel">
              Model Name <span className="optional">(optional)</span>
            </label>
            <input
              id="geminiModel"
              value={modelName}
              onChange={(e) => handleModelInput(e.target.value)}
              placeholder="default: gemini-2.5-flash"
            />
          </div>
        )}

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
        {!isLoggedIn && (
          <div className="form-prereq">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <span>
              <button type="button" className="inline-link" onClick={onLogin}>Sign in with GitHub</button> to get started
            </span>
          </div>
        )}

        {isLoggedIn && !isIndexed && (
          <div className="form-prereq">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <span>
              <button type="button" className="inline-link" onClick={onOpenIndexModal}>Index a repository</button> before generating fixes
            </span>
          </div>
        )}

        {isLoggedIn && isIndexed && repoName && (
          <div className="form-repo-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
            <span>{repoName}</span>
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={!canGenerate}
        >
          {loading && <span className="spinner-inline" />}
          {loading ? "Generating..." : "Generate Fix"}
        </button>
      </form>
    </section>
  );
}

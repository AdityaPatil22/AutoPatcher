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
    maxContextFiles,
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
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
        >
          {loading && <span className="spinner-inline" />}
          {loading ? "Generating..." : "Generate Fix"}
        </button>
      </form>
    </section>
  );
}

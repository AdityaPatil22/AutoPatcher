import { useState } from "react";
import type { UseSettingsReturn } from "../../hooks/useSettings";
import type { UsePatchGenerationReturn } from "../../hooks/usePatchGeneration";
import ProviderSelector from "../ProviderSelector/ProviderSelector";
import "./InputPanel.css";

interface InputPanelProps {
  settings: UseSettingsReturn;
  patchGen: UsePatchGenerationReturn;
  isLoggedIn: boolean;
  isIndexed: boolean;
  onLogin: () => void;
  onOpenIndexModal: () => void;
}

interface FieldErrors {
  title?: string;
  description?: string;
}

const TITLE_MAX = 200;
const DESC_MIN = 20;
const DESC_MAX = 5000;

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
    geminiRequestsRemaining,
    geminiDailyLimit,
    handleProviderChange,
    handleModelInput,
    handleMaxContextFilesChange,
  } = settings;

  const { ticket, setTicket, fileHint, setFileHint, loading, handleGenerateFix } = patchGen;

  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  function validateField(field: "title" | "description", value: string): string | undefined {
    if (field === "title") {
      if (!value.trim()) return "Title is required";
      if (value.length > TITLE_MAX) return `Title must be under ${TITLE_MAX} characters`;
    }
    if (field === "description") {
      if (!value.trim()) return "Description is required";
      if (value.trim().length < DESC_MIN) return `Description needs at least ${DESC_MIN} characters`;
      if (value.length > DESC_MAX) return `Description must be under ${DESC_MAX} characters`;
    }
    return undefined;
  }

  function handleFieldChange(field: "title" | "description", value: string) {
    setTicket((t) => ({ ...t, [field]: value }));
    if (touched[field]) {
      setFieldErrors((prev) => ({ ...prev, [field]: validateField(field, value) }));
    }
  }

  function handleBlur(field: "title" | "description") {
    setTouched((prev) => ({ ...prev, [field]: true }));
    const value = field === "title" ? ticket.title : ticket.description;
    setFieldErrors((prev) => ({ ...prev, [field]: validateField(field, value) }));
  }

  function handleSubmit(e?: React.FormEvent) {
    if (e) e.preventDefault();
    const titleErr = validateField("title", ticket.title);
    const descErr = validateField("description", ticket.description);
    setFieldErrors({ title: titleErr, description: descErr });
    setTouched({ title: true, description: true });
    if (titleErr || descErr) return;
    handleGenerateFix();
  }

  const canGenerate = isLoggedIn && isIndexed && !loading;
  const hasErrors = !!(fieldErrors.title || fieldErrors.description);

  return (
    <section className="panel input-panel">
      <h2>Bug Details</h2>
      <form onSubmit={handleSubmit} noValidate>
        <div className={`form-group ${fieldErrors.title ? "form-group-error" : ""}`}>
          <div className="label-row">
            <label htmlFor="title">Title</label>
            <span className={`char-count ${ticket.title.length > TITLE_MAX ? "char-count-over" : ""}`}>
              {ticket.title.length}/{TITLE_MAX}
            </span>
          </div>
          <input
            id="title"
            value={ticket.title}
            onChange={(e) => handleFieldChange("title", e.target.value)}
            onBlur={() => handleBlur("title")}
            placeholder="e.g. Fix export button issue"
            className={fieldErrors.title ? "input-error" : ""}
            aria-invalid={!!fieldErrors.title}
            aria-describedby={fieldErrors.title ? "title-error" : undefined}
          />
          {fieldErrors.title && (
            <div className="field-error" id="title-error" role="alert">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              {fieldErrors.title}
            </div>
          )}
        </div>

        <div className={`form-group ${fieldErrors.description ? "form-group-error" : ""}`}>
          <div className="label-row">
            <label htmlFor="description">Description</label>
            <span className={`char-count ${ticket.description.length > DESC_MAX ? "char-count-over" : ticket.description.trim().length > 0 && ticket.description.trim().length < DESC_MIN ? "char-count-warn" : ""}`}>
              {ticket.description.length}/{DESC_MAX}
            </span>
          </div>
          <textarea
            id="description"
            value={ticket.description}
            onChange={(e) => handleFieldChange("description", e.target.value)}
            onBlur={() => handleBlur("description")}
            rows={6}
            placeholder="Describe the bug in detail — what happens, what should happen, and any relevant context..."
            className={fieldErrors.description ? "input-error" : ""}
            aria-invalid={!!fieldErrors.description}
            aria-describedby={fieldErrors.description ? "desc-error" : undefined}
          />
          {fieldErrors.description && (
            <div className="field-error" id="desc-error" role="alert">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              {fieldErrors.description}
            </div>
          )}
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

        <ProviderSelector
          provider={llmProvider}
          onChange={handleProviderChange}
          modelName={modelName}
          onModelChange={handleModelInput}
          geminiRemaining={geminiRequestsRemaining}
          geminiLimit={geminiDailyLimit}
        />

        <div className="form-group">
          <label htmlFor="maxFiles">
            Max Context Files
            <span className="optional"> (1-20)</span>
          </label>
          <div className="stepper">
            <button
              type="button"
              className="stepper-btn"
              onClick={() => handleMaxContextFilesChange(maxContextFiles - 1)}
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
              onClick={() => handleMaxContextFilesChange(maxContextFiles + 1)}
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
          disabled={!canGenerate || hasErrors}
        >
          {loading && <span className="spinner-inline" />}
          {loading ? "Generating..." : "Generate Fix"}
        </button>
      </form>
    </section>
  );
}

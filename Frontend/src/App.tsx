import { useCallback, useEffect, useRef, useState } from "react";
import {
  generateFix,
  getIndexStatus,
  getSettings,
  refineFix,
  setApiKey,
  setMaxContextFiles,
  setModel,
  setProvider,
  setSearchMode,
} from "./api";
import FileTree from "./components/FileTree";
import IndexModal from "./components/IndexModal";
import PatchCard from "./components/PatchCard";
import type {
  CloudService,
  LLMProvider,
  PatchOutput,
  SearchMode,
  TicketInput,
} from "./types";
import "./App.css";

export default function App() {
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
  const [showIndexModal, setShowIndexModal] = useState(false);
  const [treeRefreshKey, setTreeRefreshKey] = useState(0);

  const [indexState, setIndexState] = useState<
    "checking" | "ready" | "empty" | "error"
  >("checking");
  const [indexChunks, setIndexChunks] = useState(0);
  const [searchMode, setSearchModeState] = useState<SearchMode>("hybrid");
  const [maxContextFiles, setMaxContextFilesState] = useState(3);

  const [llmProvider, setLlmProvider] = useState<LLMProvider>("local");
  const [modelName, setModelName] = useState("");
  const [cloudService, setCloudService] = useState<CloudService>("openai");
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [openaiKeyHint, setOpenaiKeyHint] = useState("");
  const [geminiKeyHint, setGeminiKeyHint] = useState("");
  const [keySaved, setKeySaved] = useState(false);

  const [theme, setTheme] = useState<"dark" | "light">(() => {
    return (localStorage.getItem("theme") as "dark" | "light") || "dark";
  });

  const modelDebounce = useRef<ReturnType<typeof setTimeout>>(undefined);
  const loadingTimers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const fetchIndex = useCallback(async () => {
    try {
      const data = await getIndexStatus();
      if (data.indexed && data.total_chunks > 0) {
        setIndexState("ready");
        setIndexChunks(data.total_chunks);
      } else {
        setIndexState("empty");
      }
    } catch {
      setIndexState("error");
    }
  }, []);

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

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    fetchIndex();
    fetchSettings();
  }, [fetchIndex, fetchSettings]);

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

  const indexStatusText =
    indexState === "ready"
      ? `Indexed (${indexChunks} chunks)`
      : indexState === "empty"
        ? "Not indexed"
        : indexState === "error"
          ? "Backend offline"
          : "Checking...";

  const currentKeyHint =
    cloudService === "openai" ? openaiKeyHint : geminiKeyHint;

  return (
    <div className="app">
      <header className="top-bar">
        <div className="logo">
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
          <span>AutoPatch AI</span>
        </div>
        <div className="top-actions">
          <div className={`index-status ${indexState}`}>
            <span className="status-dot" />
            <span>{indexStatusText}</span>
          </div>
          <button
            className="theme-toggle"
            onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
            type="button"
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
              </svg>
            )}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setShowIndexModal(true)}
            type="button"
          >
            Index Repository
          </button>
        </div>
      </header>

      <main className="layout">
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
                      onClick={() => {
                        setCloudService("openai");
                        setApiKeyInput("");
                        setKeySaved(false);
                      }}
                    >
                      OpenAI
                    </button>
                    <button
                      type="button"
                      className={`mode-btn ${cloudService === "gemini" ? "active" : ""}`}
                      onClick={() => {
                        setCloudService("gemini");
                        setApiKeyInput("");
                        setKeySaved(false);
                      }}
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
                        setKeySaved(false);
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

        <section className="panel output-panel">
          {error && (
            <div className="error-card">
              <div className="error-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
              </div>
              <div className="error-content">
                <div className="error-title">Something went wrong</div>
                <div className="error-detail">{error}</div>
              </div>
              <div className="error-actions">
                <button
                  className="btn btn-sm"
                  onClick={() => { setError(""); handleGenerateFix(); }}
                  type="button"
                >
                  Try Again
                </button>
                <button
                  className="error-dismiss"
                  onClick={() => setError("")}
                  type="button"
                  aria-label="Dismiss"
                >
                  &times;
                </button>
              </div>
            </div>
          )}

          <FileTree refreshKey={treeRefreshKey} />

          {!result && !loading && (
            <div className="empty-state">
              <svg
                width="64"
                height="64"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                opacity="0.3"
              >
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                <polyline points="14,2 14,8 20,8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
              <p>Submit a bug ticket to generate patches</p>
            </div>
          )}

          {(loading || refineLoading) && (
            <div className="loading-overlay">
              {refineLoading ? (
                <>
                  <div className="spinner" />
                  <p>Refining patches with your feedback...</p>
                </>
              ) : (
                <>
                  <div className="loading-steps">
                    {[
                      { label: "Searching files", icon: "search" },
                      { label: "Analyzing code", icon: "analyze" },
                      { label: "Generating patches", icon: "generate" },
                    ].map((step, i) => (
                      <div key={step.icon} className="loading-step-row">
                        {i > 0 && (
                          <div className={`step-connector ${loadingStep >= i ? "done" : ""}`} />
                        )}
                        <div className={`step-item ${loadingStep === i ? "active" : ""} ${loadingStep > i ? "done" : ""}`}>
                          <div className="step-dot">
                            {loadingStep > i ? (
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="20 6 9 17 4 12" />
                              </svg>
                            ) : (
                              <span className="step-number">{i + 1}</span>
                            )}
                          </div>
                          <span className="step-label">{step.label}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="loading-bar">
                    <div className="loading-bar-fill" />
                  </div>
                </>
              )}
            </div>
          )}

          {result && (
            <div className="results">
              <div className="results-header">
                <h2>{result.ticket_title}</h2>
                <div className="results-actions">
                  <span className="patch-count">
                    {result.patches.length} file
                    {result.patches.length !== 1 ? "s" : ""} patched
                  </span>
                  <button
                    className={`btn btn-sm ${showRawJson ? "active" : ""}`}
                    onClick={() => setShowRawJson(!showRawJson)}
                    type="button"
                  >
                    {showRawJson ? "Hide" : "Show"} JSON
                  </button>
                </div>
              </div>

              <div className="explanation-card">
                <h3>Explanation</h3>
                <p>{result.explanation}</p>
              </div>

              {showRawJson && (
                <div className="raw-json">
                  <pre>
                    <code>{JSON.stringify(result, null, 2)}</code>
                  </pre>
                </div>
              )}

              {result.patches.map((patch, idx) => (
                <PatchCard
                  key={`${patch.file_path}-${idx}`}
                  patch={patch}
                  defaultExpanded={idx === 0}
                />
              ))}

              {result.patches.length === 0 && (
                <div className="no-patches">
                  LLM did not return any file patches.
                </div>
              )}
            </div>
          )}
        </section>
      </main>

      <IndexModal
        open={showIndexModal}
        onClose={() => setShowIndexModal(false)}
        onIndexed={() => {
          fetchIndex();
          setTreeRefreshKey((k) => k + 1);
        }}
      />
    </div>
  );
}

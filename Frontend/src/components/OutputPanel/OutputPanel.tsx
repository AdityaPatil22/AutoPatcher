import { useEffect, useState } from "react";
import { createPR } from "../../api/patches";
import type { CreatePRResponse, PatchOutput } from "../../types";
import ErrorCard from "../ErrorCard/ErrorCard";
import FileTree from "../FileTree/FileTree";
import LoadingOverlay from "../LoadingOverlay/LoadingOverlay";
import PatchCard from "../PatchCard/PatchCard";
import "./OutputPanel.css";

interface OutputPanelProps {
  error: string;
  setError: (msg: string) => void;
  loading: boolean;
  loadingStep: number;
  refineLoading: boolean;
  result: PatchOutput | null;
  showRawJson: boolean;
  setShowRawJson: (v: boolean) => void;
  treeRefreshKey: number;
  handleGenerateFix: () => void;
  feedback: string;
  setFeedback: (v: string) => void;
  handleRefineFix: () => void;
  hasRepoScope: boolean;
  isLoggedIn: boolean;
  indexState: "checking" | "ready" | "empty" | "error";
  onLogin: () => void;
  onOpenIndexModal: () => void;
  repoName: string | null;
}

export default function OutputPanel({
  error,
  setError,
  loading,
  loadingStep,
  refineLoading,
  result,
  showRawJson,
  treeRefreshKey,
  handleGenerateFix,
  feedback,
  setFeedback,
  handleRefineFix,
  hasRepoScope,
  isLoggedIn,
  indexState,
  onLogin,
  onOpenIndexModal,
  repoName,
}: OutputPanelProps) {
  const [refineOpen, setRefineOpen] = useState(false);
  const [prLoading, setPrLoading] = useState(false);
  const [prResult, setPrResult] = useState<CreatePRResponse | null>(null);
  const [prError, setPrError] = useState("");

  useEffect(() => {
    setPrResult(null);
    setPrError("");
  }, [result]);

  async function handleCreatePR() {
    if (!result || result.patches.length === 0) return;
    if (!hasRepoScope) {
      window.location.href = "/api/auth/github";
      return;
    }
    setPrLoading(true);
    setPrError("");
    setPrResult(null);
    try {
      const res = await createPR({
        ticket_title: result.ticket_title,
        explanation: result.explanation,
        patches: result.patches,
      });
      setPrResult(res);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to create PR";
      if (msg.includes("log in again") || msg.includes("re-login")) {
        window.location.href = "/api/auth/github";
        return;
      }
      setPrError(msg);
    } finally {
      setPrLoading(false);
    }
  }

  const stepsDone = {
    login: isLoggedIn,
    index: indexState === "ready",
    describe: false,
  };

  return (
    <section className="panel output-panel">
      {error && (
        <ErrorCard
          message={error}
          onRetry={() => {
            setError("");
            handleGenerateFix();
          }}
          onDismiss={() => setError("")}
        />
      )}

      <FileTree refreshKey={treeRefreshKey} />

      {!result && !loading && (
        <div className="empty-state">
          <div className="onboarding">
            <h3 className="onboarding-title">How it works</h3>
            <p className="onboarding-subtitle">
              AutoPatch AI generates code fixes from bug descriptions and opens PRs for you.
            </p>
            <div className="onboarding-steps">
              <div className={`onboarding-step ${stepsDone.login ? "done" : "active"}`}>
                <div className="onboarding-step-num">{stepsDone.login ? "\u2713" : "1"}</div>
                <div className="onboarding-step-body">
                  <span className="onboarding-step-label">Sign in with GitHub</span>
                  <span className="onboarding-step-desc">
                    {stepsDone.login ? "You're signed in" : "Connect your GitHub account to get started"}
                  </span>
                  {!stepsDone.login && (
                    <button className="btn btn-sm onboarding-action" onClick={onLogin} type="button">
                      Sign in
                    </button>
                  )}
                </div>
              </div>
              <div className={`onboarding-step ${stepsDone.index ? "done" : stepsDone.login ? "active" : ""}`}>
                <div className="onboarding-step-num">{stepsDone.index ? "\u2713" : "2"}</div>
                <div className="onboarding-step-body">
                  <span className="onboarding-step-label">Index a repository</span>
                  <span className="onboarding-step-desc">
                    {stepsDone.index
                      ? `Repository indexed${repoName ? `: ${repoName}` : ""}`
                      : "Point AutoPatch to your codebase so it can understand the code"}
                  </span>
                  {!stepsDone.index && stepsDone.login && (
                    <button className="btn btn-sm onboarding-action" onClick={onOpenIndexModal} type="button">
                      Index repo
                    </button>
                  )}
                </div>
              </div>
              <div className={`onboarding-step ${stepsDone.index && stepsDone.login ? "active" : ""}`}>
                <div className="onboarding-step-num">3</div>
                <div className="onboarding-step-body">
                  <span className="onboarding-step-label">Describe a bug &amp; generate fix</span>
                  <span className="onboarding-step-desc">
                    Fill in the bug details to generate a fix.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {(loading || refineLoading) && (
        <LoadingOverlay refineLoading={refineLoading} loadingStep={loadingStep} />
      )}

      {result && (
        <div className="results">
          <div className="results-header">
            <div className="results-title-row">
              <h2>{result.ticket_title}</h2>
              <span className="patch-count">
                {result.patches.length} file
                {result.patches.length !== 1 ? "s" : ""} patched
              </span>
            </div>
            <div className="results-actions">
              <button
                className={`btn-refine ${refineOpen ? "open" : ""}`}
                onClick={() => setRefineOpen(!refineOpen)}
                type="button"
                title="Provide feedback to regenerate the fix"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
                Refine
              </button>
              <button
                className="btn-create-pr"
                onClick={handleCreatePR}
                disabled={prLoading || !!prResult}
                type="button"
                title={repoName ? `Open PR on ${repoName}` : "Create a Pull Request on GitHub"}
              >
                {prLoading ? (
                  <>
                    <span className="spinner-inline" />
                    Creating PR…
                  </>
                ) : prResult ? (
                  <>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    PR Created
                  </>
                ) : (
                  <>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="18" cy="18" r="3" />
                      <circle cx="6" cy="6" r="3" />
                      <path d="M13 6h3a2 2 0 012 2v7" />
                      <line x1="6" y1="9" x2="6" y2="21" />
                    </svg>
                    Create PR
                  </>
                )}
              </button>
            </div>
          </div>

          {prResult && (
            <div className="pr-success-banner">
              <div className="pr-success-content">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="18" cy="18" r="3" />
                  <circle cx="6" cy="6" r="3" />
                  <path d="M13 6h3a2 2 0 012 2v7" />
                  <line x1="6" y1="9" x2="6" y2="21" />
                </svg>
                <div className="pr-success-text">
                  <strong>Pull Request #{prResult.pr_number}</strong>
                  <span>Branch: <code>{prResult.branch}</code></span>
                </div>
              </div>
              <a href={prResult.pr_url} target="_blank" rel="noopener noreferrer" className="pr-link">
                View on GitHub &rarr;
              </a>
            </div>
          )}

          {prError && (
            <div className="pr-error-banner">
              <span>{prError}</span>
              <button type="button" className="pr-error-dismiss" onClick={() => setPrError("")}>&times;</button>
            </div>
          )}

          {refineOpen && (
            <div className="refine-drawer">
              <div className="refine-drawer-header">
                <div className="refine-drawer-title">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                  <span>Refine this fix</span>
                </div>
                <button
                  className="refine-drawer-close"
                  onClick={() => setRefineOpen(false)}
                  type="button"
                  aria-label="Close"
                >
                  &times;
                </button>
              </div>
              <p className="refine-drawer-hint">
                Describe what should change and we'll regenerate the patches.
              </p>
              <textarea
                className="refine-textarea"
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                rows={3}
                placeholder="e.g. The fix should also handle the edge case where..."
              />
              <button
                className="btn btn-primary refine-submit"
                onClick={() => {
                  handleRefineFix();
                  setRefineOpen(false);
                }}
                disabled={refineLoading || !feedback.trim()}
                type="button"
              >
                {refineLoading && <span className="spinner-inline" />}
                {refineLoading ? "Refining..." : "Refine Fix"}
              </button>
            </div>
          )}

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
  );
}

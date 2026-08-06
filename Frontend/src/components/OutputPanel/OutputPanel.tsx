import { useState } from "react";
import type { PatchOutput } from "../../types";
import ErrorCard from "../ErrorCard/ErrorCard";
import FileTree from "../FileTree/FileTree";
import LoadingOverlay from "../LoadingOverlay/LoadingOverlay";
import PatchCard from "../PatchCard/PatchCard";
import PRActions from "../PRActions/PRActions";
import RefineDrawer from "../RefineDrawer/RefineDrawer";
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

  const stepsDone = {
    login: isLoggedIn,
    index: indexState === "ready",
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
            <h3 className="onboarding__title">How it works</h3>
            <p className="onboarding__subtitle">
              AutoPatcher generates code fixes from bug descriptions and opens PRs for you.
            </p>
            <div className="onboarding__steps">
              <div className={`onboarding__step ${stepsDone.login ? "done" : "active"}`}>
                <div className="onboarding__step-num">{stepsDone.login ? "✓" : "1"}</div>
                <div className="onboarding__step-body">
                  <span className="onboarding__step-label">Sign in with GitHub</span>
                  <span className="onboarding__step-desc">
                    {stepsDone.login ? "You're signed in" : "Connect your GitHub account to get started"}
                  </span>
                  {!stepsDone.login && (
                    <button className="btn btn-sm onboarding__action" onClick={onLogin} type="button">
                      Sign in
                    </button>
                  )}
                </div>
              </div>
              <div className={`onboarding__step ${stepsDone.index ? "done" : stepsDone.login ? "active" : ""}`}>
                <div className="onboarding__step-num">{stepsDone.index ? "✓" : "2"}</div>
                <div className="onboarding__step-body">
                  <span className="onboarding__step-label">Index a repository</span>
                  <span className="onboarding__step-desc">
                    {stepsDone.index
                      ? `Repository indexed${repoName ? `: ${repoName}` : ""}`
                      : "Point AutoPatch to your codebase so it can understand the code"}
                  </span>
                  {!stepsDone.index && stepsDone.login && (
                    <button className="btn btn-sm onboarding__action" onClick={onOpenIndexModal} type="button">
                      Index repo
                    </button>
                  )}
                </div>
              </div>
              <div className={`onboarding__step ${stepsDone.index && stepsDone.login ? "active" : ""}`}>
                <div className="onboarding__step-num">3</div>
                <div className="onboarding__step-body">
                  <span className="onboarding__step-label">Describe a bug &amp; generate fix</span>
                  <span className="onboarding__step-desc">
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
          <div className="results__header">
            <div className="results__title-row">
              <h2>{result.ticket_title}</h2>
              <span className="results__patch-count">
                {result.patches.length} file
                {result.patches.length !== 1 ? "s" : ""} patched
              </span>
            </div>
            <div className="results__actions">
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
              <PRActions
                result={result}
                hasRepoScope={hasRepoScope}
                repoName={repoName}
              />
            </div>
          </div>

          {refineOpen && (
            <RefineDrawer
              feedback={feedback}
              onFeedbackChange={setFeedback}
              onSubmit={() => {
                handleRefineFix();
                setRefineOpen(false);
              }}
              onClose={() => setRefineOpen(false)}
              loading={refineLoading}
            />
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

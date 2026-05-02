import { useState } from "react";
import { indexRepository } from "../../api/indexing";
import type { IndexResult } from "../../types";
import "./IndexModal.css";

type Phase = "idle" | "indexing" | "success" | "error";
type SourceTab = "local" | "github";

const GITHUB_URL_RE = /^https:\/\/github\.com\/[\w.\-]+\/[\w.\-]+\/?$/;

interface Props {
  open: boolean;
  onClose: () => void;
  onIndexed: () => void;
}

export default function IndexModal({ open, onClose, onIndexed }: Props) {
  const [tab, setTab] = useState<SourceTab>("github");
  const [repoPath, setRepoPath] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<IndexResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  if (!open) return null;

  const canSubmit =
    tab === "local" ? !!repoPath.trim() : GITHUB_URL_RE.test(githubUrl.trim());

  function handleClose() {
    if (phase !== "indexing") {
      setPhase("idle");
      setResult(null);
      setErrorMsg("");
    }
    onClose();
  }

  async function handleIndex() {
    if (!canSubmit) return;
    setPhase("indexing");
    setResult(null);
    setErrorMsg("");

    try {
      const data =
        tab === "local"
          ? await indexRepository(repoPath.trim())
          : await indexRepository(undefined, githubUrl.trim());
      setResult(data);
      setPhase("success");
      onIndexed();
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Indexing failed");
      setPhase("error");
    }
  }

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
              <line x1="12" y1="11" x2="12" y2="17" />
              <line x1="9" y1="14" x2="15" y2="14" />
            </svg>
          </div>
          <div>
            <h3>Index Repository</h3>
            <p className="modal-subtitle">
              Scan source files for semantic code search
            </p>
          </div>
        </div>

        {phase === "idle" && (
          <>
            <div className="modal-tabs">
              <button
                type="button"
                className={`modal-tab ${tab === "github" ? "active" : ""}`}
                onClick={() => setTab("github")}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                </svg>
                GitHub URL
              </button>
              <button
                type="button"
                className={`modal-tab ${tab === "local" ? "active" : ""}`}
                onClick={() => setTab("local")}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
                </svg>
                Local Path
              </button>
            </div>

            {tab === "github" ? (
              <div className="form-group">
                <label htmlFor="githubUrl">GitHub Repository URL</label>
                <div className="input-with-icon">
                  <svg className="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                  </svg>
                  <input
                    id="githubUrl"
                    value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                    placeholder="https://github.com/owner/repo"
                    onKeyDown={(e) => { if (e.key === "Enter") handleIndex(); }}
                  />
                </div>
                {githubUrl && !GITHUB_URL_RE.test(githubUrl.trim()) && (
                  <p className="field-hint">Enter a valid GitHub URL: https://github.com/owner/repo</p>
                )}
              </div>
            ) : (
              <div className="form-group">
                <label htmlFor="repoPath">Repository Path</label>
                <div className="input-with-icon">
                  <svg className="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
                  </svg>
                  <input
                    id="repoPath"
                    value={repoPath}
                    onChange={(e) => setRepoPath(e.target.value)}
                    placeholder="/path/to/your/project"
                    onKeyDown={(e) => { if (e.key === "Enter") handleIndex(); }}
                  />
                </div>
              </div>
            )}

            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={handleClose} type="button">
                Cancel
              </button>
              <button
                className="btn btn-primary btn-modal"
                onClick={handleIndex}
                disabled={!canSubmit}
                type="button"
              >
                Start Indexing
              </button>
            </div>
          </>
        )}

        {phase === "indexing" && (
          <div className="modal-indexing">
            <div className="modal-progress-bar">
              <div className="modal-progress-fill" />
            </div>
            <p className="modal-indexing-text">Indexing your repository...</p>
            <p className="modal-indexing-subtext">This may take a moment for large codebases</p>
          </div>
        )}

        {phase === "success" && result && (
          <>
            <div className="modal-success-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <p className="modal-success-title">Repository indexed successfully</p>
            <div className="modal-stats">
              <div className="modal-stat">
                <span className="modal-stat-value">{result.files_indexed}</span>
                <span className="modal-stat-label">Files Indexed</span>
              </div>
              <div className="modal-stat">
                <span className="modal-stat-value">{result.chunks_created}</span>
                <span className="modal-stat-label">Chunks Created</span>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn btn-primary btn-modal" onClick={handleClose} type="button">
                Done
              </button>
            </div>
          </>
        )}

        {phase === "error" && (
          <>
            <div className="modal-error-banner">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{errorMsg}</span>
            </div>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={handleClose} type="button">
                Cancel
              </button>
              <button
                className="btn btn-primary btn-modal"
                onClick={() => { setPhase("idle"); }}
                type="button"
              >
                Try Again
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

import { useState } from "react";
import { clearIndex, indexRepository } from "../../api/indexing";
import type { IndexResult } from "../../types";
import "./IndexModal.css";

type Phase = "idle" | "indexing" | "success" | "error" | "confirm-clear" | "clearing" | "cleared";

const GITHUB_URL_RE = /^https:\/\/github\.com\/[\w.\-]+\/[\w.\-]+\/?$/;

interface Props {
  open: boolean;
  onClose: () => void;
  onIndexed: () => void;
  isIndexed: boolean;
  repoName: string | null;
}

export default function IndexModal({ open, onClose, onIndexed, isIndexed, repoName }: Props) {
  const [githubUrl, setGithubUrl] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<IndexResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  if (!open) return null;

  const canSubmit = GITHUB_URL_RE.test(githubUrl.trim());

  function handleClose() {
    if (phase !== "indexing" && phase !== "clearing") {
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
      const data = await indexRepository(githubUrl.trim());
      setResult(data);
      setPhase("success");
      onIndexed();
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Indexing failed");
      setPhase("error");
    }
  }

  async function handleClear() {
    setPhase("clearing");
    try {
      await clearIndex();
      setPhase("cleared");
      onIndexed();
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Failed to clear index");
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
            {isIndexed && repoName && (
              <div className="modal-current-repo">
                <div className="modal-current-repo-info">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
                  <span>Currently indexed: <strong>{repoName}</strong></span>
                </div>
                <button
                  type="button"
                  className="btn-clear-index"
                  onClick={() => setPhase("confirm-clear")}
                >
                  Clear Index
                </button>
              </div>
            )}

            <div className="form-group">
              <label htmlFor="githubUrl">GitHub Repository URL</label>
              <div className="input-with-icon">
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

        {phase === "confirm-clear" && (
          <>
            <div className="modal-clear-confirm">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
              </svg>
              <div>
                <p className="modal-clear-title">Clear index for {repoName}?</p>
                <p className="modal-clear-desc">This will remove all indexed data. You'll need to re-index before generating fixes.</p>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setPhase("idle")} type="button">
                Cancel
              </button>
              <button className="btn btn-danger btn-modal" onClick={handleClear} type="button">
                Clear Index
              </button>
            </div>
          </>
        )}

        {phase === "clearing" && (
          <div className="modal-indexing">
            <div className="modal-progress-bar">
              <div className="modal-progress-fill" />
            </div>
            <p className="modal-indexing-text">Clearing index...</p>
          </div>
        )}

        {phase === "cleared" && (
          <>
            <div className="modal-success-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <p className="modal-success-title">Index cleared successfully</p>
            <div className="modal-actions">
              <button className="btn btn-primary btn-modal" onClick={handleClose} type="button">
                Done
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

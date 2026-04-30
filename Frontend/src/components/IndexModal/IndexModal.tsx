import { useState } from "react";
import { indexRepository } from "../../api/indexing";
import type { IndexResult } from "../../types";
import "./IndexModal.css";

type Phase = "idle" | "indexing" | "success" | "error";

interface Props {
  open: boolean;
  onClose: () => void;
  onIndexed: () => void;
}

export default function IndexModal({ open, onClose, onIndexed }: Props) {
  const [repoPath, setRepoPath] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<IndexResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  if (!open) return null;

  function handleClose() {
    if (phase !== "indexing") {
      setPhase("idle");
      setResult(null);
      setErrorMsg("");
    }
    onClose();
  }

  async function handleIndex() {
    if (!repoPath.trim()) return;
    setPhase("indexing");
    setResult(null);
    setErrorMsg("");

    try {
      const data = await indexRepository(repoPath);
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
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={handleClose} type="button">
                Cancel
              </button>
              <button
                className="btn btn-primary btn-modal"
                onClick={handleIndex}
                disabled={!repoPath.trim()}
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

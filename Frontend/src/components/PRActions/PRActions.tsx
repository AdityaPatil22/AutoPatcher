import { useEffect, useState } from "react";
import { createPR } from "../../api/patches";
import type { CreatePRResponse, PatchOutput } from "../../types";
import "./PRActions.css";

interface PRActionsProps {
  result: PatchOutput;
  hasRepoScope: boolean;
  repoName: string | null;
}

export default function PRActions({ result, hasRepoScope, repoName }: PRActionsProps) {
  const [prLoading, setPrLoading] = useState(false);
  const [prResult, setPrResult] = useState<CreatePRResponse | null>(null);
  const [prError, setPrError] = useState("");

  useEffect(() => {
    setPrResult(null);
    setPrError("");
  }, [result]);

  async function handleCreatePR() {
    if (result.patches.length === 0) return;
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

  return (
    <>
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

      {prResult && (
        <div className="pr-success-banner">
          <div className="pr-success-banner__content">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="18" cy="18" r="3" />
              <circle cx="6" cy="6" r="3" />
              <path d="M13 6h3a2 2 0 012 2v7" />
              <line x1="6" y1="9" x2="6" y2="21" />
            </svg>
            <div className="pr-success-banner__text">
              <strong>Pull Request #{prResult.pr_number}</strong>
              <span>Branch: <code>{prResult.branch}</code></span>
            </div>
          </div>
          <a href={prResult.pr_url} target="_blank" rel="noopener noreferrer" className="pr-success-banner__link">
            View on GitHub &rarr;
          </a>
        </div>
      )}

      {prError && (
        <div className="pr-error-banner">
          <span>{prError}</span>
          <button type="button" className="pr-error-banner__dismiss" onClick={() => setPrError("")}>&times;</button>
        </div>
      )}
    </>
  );
}

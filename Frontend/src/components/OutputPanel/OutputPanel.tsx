import type { PatchOutput } from "../../types";
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
}

export default function OutputPanel({
  error,
  setError,
  loading,
  loadingStep,
  refineLoading,
  result,
  showRawJson,
  setShowRawJson,
  treeRefreshKey,
  handleGenerateFix,
}: OutputPanelProps) {
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
        <LoadingOverlay refineLoading={refineLoading} loadingStep={loadingStep} />
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
  );
}

import { useState } from "react";
import type { FilePatch } from "../../types";
import "./PatchCard.css";

const EXT_COLORS: Record<string, string> = {
  py: "#3572A5", js: "#f1e05a", ts: "#3178c6", jsx: "#f1e05a", tsx: "#3178c6",
  vue: "#41b883", java: "#b07219", go: "#00ADD8", rb: "#CC342D", rs: "#dea584",
  cpp: "#f34b7d", c: "#555555", html: "#e34c26", css: "#563d7c", svelte: "#ff3e00",
};

const EXT_LABELS: Record<string, string> = {
  py: "Python", js: "JavaScript", ts: "TypeScript", jsx: "React JSX", tsx: "React TSX",
  vue: "Vue", java: "Java", go: "Go", rb: "Ruby", rs: "Rust",
  cpp: "C++", c: "C", html: "HTML", css: "CSS", svelte: "Svelte",
};

type Tab = "diff" | "fixed" | "original";

interface Props {
  patch: FilePatch;
  defaultExpanded?: boolean;
}

function parseDiffLines(diff: string) {
  let oldLine = 0;
  let newLine = 0;

  return diff.split("\n").map((line) => {
    const hunkMatch = line.match(/^@@ -(\d+)(?:,\d+)? \+(\d+)/);
    if (hunkMatch) {
      oldLine = parseInt(hunkMatch[1], 10);
      newLine = parseInt(hunkMatch[2], 10);
      return { type: "hunk" as const, text: line, oldNum: "", newNum: "" };
    }
    if (line.startsWith("---") || line.startsWith("+++"))
      return { type: "hunk" as const, text: line, oldNum: "", newNum: "" };
    if (line.startsWith("+")) {
      const num = String(newLine++);
      return { type: "added" as const, text: line.slice(1), oldNum: "", newNum: num };
    }
    if (line.startsWith("-")) {
      const num = String(oldLine++);
      return { type: "removed" as const, text: line.slice(1), oldNum: num, newNum: "" };
    }
    const oNum = String(oldLine++);
    const nNum = String(newLine++);
    return {
      type: "context" as const,
      text: line.startsWith(" ") ? line.slice(1) : line,
      oldNum: oNum,
      newNum: nNum,
    };
  });
}

function countChanges(diff: string) {
  let added = 0;
  let removed = 0;
  for (const line of diff.split("\n")) {
    if (line.startsWith("+") && !line.startsWith("+++")) added++;
    if (line.startsWith("-") && !line.startsWith("---")) removed++;
  }
  return { added, removed };
}

export default function PatchCard({ patch, defaultExpanded = false }: Props) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [activeTab, setActiveTab] = useState<Tab>("diff");
  const [copied, setCopied] = useState(false);

  const ext = patch.file_path.split(".").pop()?.toLowerCase() ?? "";
  const color = EXT_COLORS[ext] || "var(--text-dim)";
  const lang = EXT_LABELS[ext] || ext.toUpperCase();
  const changes = patch.diff ? countChanges(patch.diff) : null;

  function handleCopy() {
    navigator.clipboard.writeText(patch.fixed_code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="patch-card">
      <button
        className="patch-header"
        onClick={() => setExpanded(!expanded)}
        type="button"
      >
        <div className="patch-title">
          <svg
            className={`chevron ${expanded ? "rotated" : ""}`}
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="9,18 15,12 9,6" />
          </svg>
          <span className="patch-ext-dot" style={{ background: color }} />
          <span className="file-path">{patch.file_path}</span>
          <span className="patch-lang">{lang}</span>
        </div>
        <div className="patch-meta">
          {changes && (
            <div className="patch-stats">
              {changes.added > 0 && <span className="stat-added">+{changes.added}</span>}
              {changes.removed > 0 && <span className="stat-removed">-{changes.removed}</span>}
            </div>
          )}
          {patch.warning && (
            <span className="warning-badge" title="Quality warning">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </span>
          )}
        </div>
      </button>

      {expanded && (
        <div className="patch-body">
          {patch.warning && (
            <div className="warning-banner">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              <span>{patch.warning}</span>
            </div>
          )}

          <div className="tab-bar">
            <div className="tab-group">
              {(
                [
                  ["diff", "Diff"],
                  ["fixed", "Fixed Code"],
                  ["original", "Original"],
                ] as const
              ).map(([key, label]) => (
                <button
                  key={key}
                  className={`tab ${activeTab === key ? "active" : ""}`}
                  onClick={() => setActiveTab(key)}
                  type="button"
                >
                  {label}
                </button>
              ))}
            </div>
            {activeTab === "fixed" && (
              <button
                className={`copy-btn ${copied ? "copied" : ""}`}
                onClick={handleCopy}
                type="button"
              >
                {copied ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                    <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
                  </svg>
                )}
                {copied ? "Copied" : "Copy"}
              </button>
            )}
          </div>

          <div className="code-view">
            {activeTab === "diff" ? (
              patch.diff ? (
                <div className="diff-view">
                  {parseDiffLines(patch.diff).map((line, i) => (
                    <div key={i} className={`diff-line ${line.type}`}>
                      <span className="diff-ln">
                        {line.type === "removed" ? line.oldNum : line.newNum}
                      </span>
                      <span className="diff-prefix">
                        {line.type === "added"
                          ? "+"
                          : line.type === "removed"
                            ? "-"
                            : " "}
                      </span>
                      <span className="diff-text">{line.text}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-diff">No differences detected.</p>
              )
            ) : (
              <pre className="code-block">
                <code>
                  {activeTab === "fixed"
                    ? patch.fixed_code
                    : patch.original_code}
                </code>
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

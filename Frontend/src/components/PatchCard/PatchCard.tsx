import { useState } from "react";
import type { FilePatch } from "../../types";
import "./PatchCard.css";

const FILE_ICONS: Record<string, string> = {
  py: "\u{1F40D}",
  js: "\u{1F7E8}",
  ts: "\u{1F535}",
  jsx: "⚡",
  tsx: "⚡",
  vue: "\u{1F49A}",
  java: "☕",
  go: "\u{1F439}",
  rb: "\u{1F48E}",
  rs: "⚙️",
  cpp: "\u{1F1E8}",
  c: "\u{1F1E8}",
  html: "\u{1F310}",
  css: "\u{1F3A8}",
};

type Tab = "diff" | "fixed" | "original";

interface Props {
  patch: FilePatch;
  defaultExpanded?: boolean;
}

function parseDiffLines(diff: string) {
  return diff.split("\n").map((line) => {
    if (line.startsWith("@@"))
      return { type: "hunk" as const, text: line };
    if (line.startsWith("---") || line.startsWith("+++"))
      return { type: "hunk" as const, text: line };
    if (line.startsWith("+"))
      return { type: "added" as const, text: line.slice(1) };
    if (line.startsWith("-"))
      return { type: "removed" as const, text: line.slice(1) };
    return {
      type: "context" as const,
      text: line.startsWith(" ") ? line.slice(1) : line,
    };
  });
}

export default function PatchCard({ patch, defaultExpanded = false }: Props) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [activeTab, setActiveTab] = useState<Tab>("diff");

  const ext = patch.file_path.split(".").pop()?.toLowerCase() ?? "";
  const icon = FILE_ICONS[ext] || "\u{1F4C4}";

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
          <span className="file-icon">{icon}</span>
          <span className="file-path">{patch.file_path}</span>
        </div>
        {patch.warning && (
          <span className="warning-badge" title="Quality warning">
            !
          </span>
        )}
      </button>

      {expanded && (
        <div className="patch-body">
          {patch.warning && (
            <div className="warning-banner">
              <strong>Warning:</strong> {patch.warning}
            </div>
          )}

          <div className="tab-bar">
            {(
              [
                ["diff", "Diff"],
                ["fixed", "Fixed Code"],
                ["original", "Original Code"],
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

          <div className="code-view">
            {activeTab === "diff" ? (
              patch.diff ? (
                <div className="diff-view">
                  {parseDiffLines(patch.diff).map((line, i) => (
                    <div key={i} className={`diff-line ${line.type}`}>
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

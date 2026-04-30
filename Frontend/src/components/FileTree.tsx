import { useEffect, useState } from "react";
import { getIndexFiles } from "../api";
import type { FileNode } from "../types";

const EXT_ICONS: Record<string, string> = {
  py: "\u{1F40D}",
  js: "\u{1F7E8}",
  ts: "\u{1F535}",
  jsx: "\u26A1",
  tsx: "\u26A1",
  vue: "\u{1F49A}",
  java: "\u2615",
  go: "\u{1F439}",
  rb: "\u{1F48E}",
  rs: "\u2699\uFE0F",
  cpp: "\u{1F1E8}",
  c: "\u{1F1E8}",
  html: "\u{1F310}",
  css: "\u{1F3A8}",
  json: "\u{1F4CB}",
  svelte: "\u{1F525}",
  kt: "\u{1F7E3}",
  swift: "\u{1F34A}",
};

function getIcon(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  return EXT_ICONS[ext] || "\u{1F4C4}";
}

function TreeNode({ node, depth = 0 }: { node: FileNode; depth?: number }) {
  const [open, setOpen] = useState(depth < 2);

  if (node.type === "file") {
    return (
      <div className="tree-file" style={{ paddingLeft: depth * 16 }}>
        <span className="tree-icon">{getIcon(node.name)}</span>
        <span className="tree-name">{node.name}</span>
      </div>
    );
  }

  return (
    <div className="tree-folder-wrapper">
      <button
        className="tree-folder"
        style={{ paddingLeft: depth * 16 }}
        onClick={() => setOpen(!open)}
        type="button"
      >
        <svg
          className={`tree-chevron ${open ? "open" : ""}`}
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
        >
          <polyline points="9,18 15,12 9,6" />
        </svg>
        <span className="tree-icon">{open ? "\u{1F4C2}" : "\u{1F4C1}"}</span>
        <span className="tree-name">{node.name}</span>
        {node.children && (
          <span className="tree-count">{countFiles(node)}</span>
        )}
      </button>
      {open && node.children && (
        <div className="tree-children">
          {node.children.map((child) => (
            <TreeNode key={child.name} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function countFiles(node: FileNode): number {
  if (node.type === "file") return 1;
  return (node.children ?? []).reduce((sum, c) => sum + countFiles(c), 0);
}

interface Props {
  refreshKey: number;
}

export default function FileTree({ refreshKey }: Props) {
  const [tree, setTree] = useState<FileNode[]>([]);
  const [totalFiles, setTotalFiles] = useState(0);
  const [root, setRoot] = useState("");
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    setLoading(true);
    getIndexFiles()
      .then((data) => {
        setTree(data.tree);
        setTotalFiles(data.total_files);
        setRoot(data.root || "");
      })
      .catch(() => {
        setTree([]);
        setTotalFiles(0);
      })
      .finally(() => setLoading(false));
  }, [refreshKey]);

  if (loading) {
    return (
      <div className="file-tree-panel">
        <div className="tree-loading">Loading files...</div>
      </div>
    );
  }

  if (totalFiles === 0) {
    return null;
  }

  return (
    <div className="file-tree-panel">
      <button
        className="file-tree-header"
        onClick={() => setExpanded(!expanded)}
        type="button"
      >
        <div className="file-tree-title">
          <svg
            className={`tree-chevron ${expanded ? "open" : ""}`}
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
          >
            <polyline points="9,18 15,12 9,6" />
          </svg>
          <span>Indexed Files</span>
          <span className="tree-badge">{totalFiles}</span>
        </div>
        {root && <span className="tree-root">{root}</span>}
      </button>
      {expanded && (
        <div className="file-tree-body">
          {tree.map((node) => (
            <TreeNode key={node.name} node={node} />
          ))}
        </div>
      )}
    </div>
  );
}

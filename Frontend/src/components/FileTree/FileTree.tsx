import { useEffect, useMemo, useState } from "react";
import { getIndexFiles } from "../../api/indexing";
import type { FileNode } from "../../types";
import { EXT_COLORS } from "../../constants/fileExtensions";
import "./FileTree.css";

function ExtDot({ name }: { name: string }) {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  const color = EXT_COLORS[ext] || "var(--text-dim)";
  return (
    <span
      className="tree-ext-dot"
      style={{ background: color }}
    />
  );
}

function countFiles(node: FileNode): number {
  if (node.type === "file") return 1;
  return (node.children ?? []).reduce((sum, c) => sum + countFiles(c), 0);
}

function filterTree(nodes: FileNode[], query: string): FileNode[] {
  if (!query) return nodes;
  const q = query.toLowerCase();
  return nodes.reduce<FileNode[]>((acc, node) => {
    if (node.type === "file") {
      if (node.name.toLowerCase().includes(q)) acc.push(node);
    } else {
      const filteredChildren = filterTree(node.children ?? [], query);
      if (filteredChildren.length > 0) {
        acc.push({ ...node, children: filteredChildren });
      }
    }
    return acc;
  }, []);
}

function TreeNode({
  node,
  depth = 0,
  forceExpanded,
}: {
  node: FileNode;
  depth?: number;
  forceExpanded?: boolean;
}) {
  const [open, setOpen] = useState(forceExpanded ?? depth < 2);

  useEffect(() => {
    if (forceExpanded !== undefined) setOpen(forceExpanded);
  }, [forceExpanded]);

  if (node.type === "file") {
    return (
      <div className="tree-file" style={{ paddingLeft: 16 + depth * 16 }}>
        <ExtDot name={node.name} />
        <span className="tree-name">{node.name}</span>
      </div>
    );
  }

  return (
    <div className="tree-folder-wrapper">
      <button
        className="tree-folder"
        style={{ paddingLeft: 16 + depth * 16 }}
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
        <svg className="tree-folder-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          {open
            ? <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
            : <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
          }
        </svg>
        <span className="tree-name">{node.name}</span>
        {node.children && (
          <span className="tree-count">{countFiles(node)}</span>
        )}
      </button>
      {open && node.children && (
        <div className="tree-children">
          {node.children.map((child) => (
            <TreeNode
              key={child.name}
              node={child}
              depth={depth + 1}
              forceExpanded={forceExpanded}
            />
          ))}
        </div>
      )}
    </div>
  );
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
  const [filter, setFilter] = useState("");
  const [allExpanded, setAllExpanded] = useState<boolean | undefined>(
    undefined
  );

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

  const filteredTree = useMemo(
    () => filterTree(tree, filter),
    [tree, filter]
  );

  if (loading) {
    return (
      <div className="file-tree-panel">
        <div className="tree-loading">
          <div className="tree-loading-shimmer" />
          <div className="tree-loading-shimmer short" />
          <div className="tree-loading-shimmer" />
        </div>
      </div>
    );
  }

  if (totalFiles === 0) {
    return (
      <div className="file-tree-panel">
        <div className="tree-empty">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.4">
            <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
          </svg>
          <p>No files indexed yet</p>
          <p className="tree-empty-sub">Index a repository to see files here</p>
        </div>
      </div>
    );
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
          <span>{root ? root.split("/").filter(Boolean).pop() : "Indexed Files"}</span>
          <span className="tree-badge">{totalFiles}</span>
        </div>
      </button>
      {expanded && (
        <>
          <div className="tree-toolbar">
            <div className="tree-search">
              <svg className="tree-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                className="tree-search-input"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Filter files..."
              />
              {filter && (
                <button
                  className="tree-search-clear"
                  onClick={() => setFilter("")}
                  type="button"
                  aria-label="Clear filter"
                >
                  &times;
                </button>
              )}
            </div>
            <div className="tree-controls">
              <button
                className="tree-control-btn"
                onClick={() => setAllExpanded(true)}
                type="button"
                title="Expand all"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="7,13 12,18 17,13" />
                  <polyline points="7,6 12,11 17,6" />
                </svg>
              </button>
              <button
                className="tree-control-btn"
                onClick={() => setAllExpanded(false)}
                type="button"
                title="Collapse all"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="7,11 12,6 17,11" />
                  <polyline points="7,18 12,13 17,18" />
                </svg>
              </button>
            </div>
          </div>
          <div className="file-tree-body">
            {filteredTree.length > 0 ? (
              filteredTree.map((node) => (
                <TreeNode
                  key={node.name}
                  node={node}
                  forceExpanded={filter ? true : allExpanded}
                />
              ))
            ) : (
              <div className="tree-no-results">
                No files match "{filter}"
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

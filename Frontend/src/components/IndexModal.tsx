import { useState } from "react";
import { indexRepository } from "../api";

interface Props {
  open: boolean;
  onClose: () => void;
  onIndexed: () => void;
}

export default function IndexModal({ open, onClose, onIndexed }: Props) {
  const [repoPath, setRepoPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<"success" | "error">(
    "success"
  );

  if (!open) return null;

  async function handleIndex() {
    if (!repoPath.trim()) return;
    setLoading(true);
    setMessage("");

    try {
      const data = await indexRepository(repoPath);
      setMessage(
        data.message ||
          `Indexed ${data.files_indexed} files (${data.chunks_created} chunks)`
      );
      setMessageType("success");
      onIndexed();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Indexing failed");
      setMessageType("error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Index Repository</h3>
        <p>
          Enter the path to a local repository to index its source files for
          semantic search.
        </p>
        <div className="form-group">
          <label htmlFor="repoPath">Repository Path</label>
          <input
            id="repoPath"
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            placeholder="/path/to/your/project"
          />
        </div>
        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onClose} type="button">
            Cancel
          </button>
          <button
            className="btn btn-primary btn-modal"
            onClick={handleIndex}
            disabled={loading || !repoPath.trim()}
            type="button"
          >
            {loading && <span className="spinner-inline" />}
            {loading ? "Indexing..." : "Start Indexing"}
          </button>
        </div>
        {message && (
          <div className={`index-message ${messageType}`}>{message}</div>
        )}
      </div>
    </div>
  );
}

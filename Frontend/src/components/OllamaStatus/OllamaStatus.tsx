import { useEffect, useState } from "react";
import { isOllamaRunning, listOllamaModels } from "../../api/localLLM";
import "./OllamaStatus.css";

interface OllamaStatusProps {
  modelName: string;
  onModelChange: (model: string) => void;
}

export default function OllamaStatus({ modelName, onModelChange }: OllamaStatusProps) {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");
  const [models, setModels] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function check() {
      setStatus("checking");
      const running = await isOllamaRunning();
      if (cancelled) return;
      setStatus(running ? "online" : "offline");

      if (running) {
        const list = await listOllamaModels();
        if (!cancelled) setModels(list);
      } else {
        setModels([]);
      }
    }

    check();
    const interval = setInterval(check, 10_000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  return (
    <>
      <div className={`ollama-status ollama-${status}`}>
        <div className="ollama-status-row">
          <span className="ollama-dot" />
          <span className="ollama-label">
            {status === "checking" && "Checking Ollama..."}
            {status === "online" && "Ollama connected"}
            {status === "offline" && "Ollama not detected"}
          </span>
          {status === "online" && (
            <span className="ollama-badge">{models.length} model{models.length !== 1 ? "s" : ""}</span>
          )}
        </div>
        {status === "offline" && (
          <div className="ollama-help">
            <p>To use this feature, install and run Ollama locally on your system.</p>
            <ol className="ollama-steps">
              <li>Install from <a href="https://ollama.com" target="_blank" rel="noopener noreferrer">ollama.com</a></li>
              <li>Pull a model: <code>ollama pull llama3</code></li>
              <li>Enable browser access: <code>OLLAMA_ORIGINS=* ollama serve</code></li>
            </ol>
            <a
              className="ollama-setup-link"
              href="https://github.com/AdityaPatil22/AutoPatch-AI#setup"
              target="_blank"
              rel="noopener noreferrer"
            >
              View full setup guide
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            </a>
          </div>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="browserModel">Model</label>
        {models.length > 0 ? (
          <div className="model-select-wrapper">
            <select
              id="browserModel"
              className="model-select"
              value={modelName}
              onChange={(e) => onModelChange(e.target.value)}
            >
              {!modelName && <option value="">Select a model...</option>}
              {models.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
        ) : (
          <input
            id="browserModel"
            value={modelName}
            onChange={(e) => onModelChange(e.target.value)}
            placeholder="e.g. llama3, deepseek-coder:6.7b"
          />
        )}
      </div>
    </>
  );
}

import "./ErrorCard.css";

interface ErrorCardProps {
  message: string;
  onRetry: () => void;
  onDismiss: () => void;
}

function parseErrorMessage(raw: string): { title: string; detail: string } {
  const statusMatch = raw.match(/^(\d{3})\s+\w+/);
  const statusCode = statusMatch ? parseInt(statusMatch[1], 10) : null;

  const jsonMatch = raw.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    try {
      const parsed = JSON.parse(jsonMatch[0].replace(/'/g, '"'));
      const msg =
        parsed?.error?.message ||
        parsed?.message ||
        parsed?.detail ||
        null;
      if (msg) {
        const title = statusCode
          ? `Error ${statusCode}`
          : "Something went wrong";
        return { title, detail: msg };
      }
    } catch {
      // not valid JSON, fall through
    }
  }

  if (raw.includes("429") || raw.toLowerCase().includes("limit")) {
    return { title: "Rate limit reached", detail: raw };
  }

  if (raw.includes("503") || raw.toLowerCase().includes("unavailable")) {
    return {
      title: "Service temporarily unavailable",
      detail: "The model is experiencing high demand. Please try again in a moment.",
    };
  }

  if (raw.includes("500")) {
    return { title: "Server error", detail: "An internal error occurred. Please try again." };
  }

  return { title: "Something went wrong", detail: raw };
}

export default function ErrorCard({ message, onRetry, onDismiss }: ErrorCardProps) {
  const { title, detail } = parseErrorMessage(message);

  return (
    <div className="error-card">
      <div className="error-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      </div>
      <div className="error-content">
        <div className="error-title">{title}</div>
        <div className="error-detail">{detail}</div>
      </div>
      <div className="error-actions">
        <button className="btn btn-sm" onClick={onRetry} type="button">
          Try Again
        </button>
        <button
          className="error-dismiss"
          onClick={onDismiss}
          type="button"
          aria-label="Dismiss"
        >
          &times;
        </button>
      </div>
    </div>
  );
}

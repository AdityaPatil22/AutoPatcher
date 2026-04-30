import "./ErrorCard.css";

interface ErrorCardProps {
  message: string;
  onRetry: () => void;
  onDismiss: () => void;
}

export default function ErrorCard({ message, onRetry, onDismiss }: ErrorCardProps) {
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
        <div className="error-title">Something went wrong</div>
        <div className="error-detail">{message}</div>
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

import "./RefineDrawer.css";

interface RefineDrawerProps {
  feedback: string;
  onFeedbackChange: (v: string) => void;
  onSubmit: () => void;
  onClose: () => void;
  loading: boolean;
}

export default function RefineDrawer({
  feedback,
  onFeedbackChange,
  onSubmit,
  onClose,
  loading,
}: RefineDrawerProps) {
  return (
    <div className="refine-drawer">
      <div className="refine-drawer__header">
        <div className="refine-drawer__title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          <span>Refine this fix</span>
        </div>
        <button
          className="refine-drawer__close"
          onClick={onClose}
          type="button"
          aria-label="Close"
        >
          &times;
        </button>
      </div>
      <p className="refine-drawer__hint">
        Describe what should change and we'll regenerate the patches.
      </p>
      <textarea
        className="refine-drawer__textarea"
        value={feedback}
        onChange={(e) => onFeedbackChange(e.target.value)}
        rows={3}
        placeholder="e.g. The fix should also handle the edge case where..."
      />
      <button
        className="btn btn-primary refine-drawer__submit"
        onClick={onSubmit}
        disabled={loading || !feedback.trim()}
        type="button"
      >
        {loading && <span className="spinner-inline" />}
        {loading ? "Refining..." : "Refine Fix"}
      </button>
    </div>
  );
}

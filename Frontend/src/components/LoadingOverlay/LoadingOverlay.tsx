import "./LoadingOverlay.css";

const STEPS = [
  { label: "Searching files", icon: "search" },
  { label: "Analyzing code", icon: "analyze" },
  { label: "Generating patches", icon: "generate" },
];

interface LoadingOverlayProps {
  refineLoading: boolean;
  loadingStep: number;
}

export default function LoadingOverlay({ refineLoading, loadingStep }: LoadingOverlayProps) {
  return (
    <div className="loading-overlay">
      {refineLoading ? (
        <>
          <svg className="brace-loader" viewBox="0 0 120 60" fill="none">
            <path
              className="brace brace-left"
              d="M38 5 Q28 5 28 15 L28 24 Q28 30 22 30 Q28 30 28 36 L28 45 Q28 55 38 55"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            <path
              className="brace brace-right"
              d="M82 5 Q92 5 92 15 L92 24 Q92 30 98 30 Q92 30 92 36 L92 45 Q92 55 82 55"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          </svg>
          <p>Refining patches with your feedback...</p>
        </>
      ) : (
        <>
          <svg className="brace-loader" viewBox="0 0 120 60" fill="none">
            <path
              className="brace brace-left"
              d="M38 5 Q28 5 28 15 L28 24 Q28 30 22 30 Q28 30 28 36 L28 45 Q28 55 38 55"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            <path
              className="brace brace-right"
              d="M82 5 Q92 5 92 15 L92 24 Q92 30 98 30 Q92 30 92 36 L92 45 Q92 55 82 55"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          </svg>
          <div className="loading-steps">
            {STEPS.map((step, i) => (
              <div key={step.icon} className="loading-step-row">
                {i > 0 && (
                  <div className={`step-connector ${loadingStep >= i ? "done" : ""}`} />
                )}
                <div className={`step-item ${loadingStep === i ? "active" : ""} ${loadingStep > i ? "done" : ""}`}>
                  <div className="step-dot">
                    {loadingStep > i ? (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    ) : (
                      <span className="step-number">{i + 1}</span>
                    )}
                  </div>
                  <span className="step-label">{step.label}</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

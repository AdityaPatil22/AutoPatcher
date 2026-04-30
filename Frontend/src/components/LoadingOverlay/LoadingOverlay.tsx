import "./LoadingOverlay.css";

interface LoadingOverlayProps {
  refineLoading: boolean;
  loadingStep: number;
}

export default function LoadingOverlay({ refineLoading, loadingStep }: LoadingOverlayProps) {
  return (
    <div className="loading-overlay">
      {refineLoading ? (
        <>
          <div className="spinner" />
          <p>Refining patches with your feedback...</p>
        </>
      ) : (
        <>
          <div className="loading-steps">
            {[
              { label: "Searching files", icon: "search" },
              { label: "Analyzing code", icon: "analyze" },
              { label: "Generating patches", icon: "generate" },
            ].map((step, i) => (
              <div key={step.icon} className="loading-step-row">
                {i > 0 && (
                  <div className={`step-connector ${loadingStep >= i ? "done" : ""}`} />
                )}
                <div className={`step-item ${loadingStep === i ? "active" : ""} ${loadingStep > i ? "done" : ""}`}>
                  <div className="step-dot">
                    {loadingStep > i ? (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
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
          <div className="loading-bar">
            <div className="loading-bar-fill" />
          </div>
        </>
      )}
    </div>
  );
}

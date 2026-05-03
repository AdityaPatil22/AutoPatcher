import { useState } from "react";
import type { UseAuthReturn } from "../../hooks/useAuth";
import "./TopBar.css";

interface TopBarProps {
  indexState: "checking" | "ready" | "empty" | "error";
  indexStatusText: string;
  theme: "dark" | "light";
  toggleTheme: () => void;
  onOpenIndexModal: () => void;
  auth: UseAuthReturn;
  repoName: string | null;
}

export default function TopBar({
  indexState,
  indexStatusText,
  theme,
  toggleTheme,
  onOpenIndexModal,
  auth,
  repoName,
}: TopBarProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="top-bar">
      <div className="logo">
        <svg
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
        <span>AutoPatch AI</span>
      </div>
      <div className="top-actions">
        <button
          className={`index-status ${indexState}`}
          onClick={onOpenIndexModal}
          type="button"
          title={indexState === "ready" ? "Change indexed repository" : "Index a repository"}
        >
          <span className="status-dot" />
          <span>
            {indexState === "ready" && repoName
              ? repoName
              : indexStatusText}
          </span>
          {indexState === "ready" && (
            <span className="index-badge">indexed</span>
          )}
        </button>
        <button
          className="theme-toggle"
          onClick={toggleTheme}
          type="button"
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
            </svg>
          )}
        </button>
        {auth.isLoggedIn && auth.user ? (
          <div className="user-menu-wrapper">
            <button
              className="user-avatar-btn"
              onClick={() => setMenuOpen((o) => !o)}
              type="button"
              aria-label="User menu"
            >
              <img
                src={auth.user.avatar_url}
                alt={auth.user.username}
                className="user-avatar"
              />
              <span className="user-name">{auth.user.username}</span>
            </button>
            {menuOpen && (
              <div className="user-dropdown" onClick={() => setMenuOpen(false)}>
                <button
                  className="dropdown-item"
                  onClick={auth.logout}
                  type="button"
                >
                  Sign out
                </button>
              </div>
            )}
          </div>
        ) : (
          <button
            className="btn btn-github"
            onClick={auth.login}
            type="button"
            disabled={auth.loading}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
            Sign in with GitHub
          </button>
        )}
      </div>
    </header>
  );
}

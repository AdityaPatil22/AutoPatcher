import { useEffect, useState } from "react";
import TopBar from "./components/TopBar/TopBar";
import InputPanel from "./components/InputPanel/InputPanel";
import OutputPanel from "./components/OutputPanel/OutputPanel";
import IndexModal from "./components/IndexModal/IndexModal";
import { useTheme } from "./hooks/useTheme";
import { useIndex } from "./hooks/useIndex";
import { useSettings } from "./hooks/useSettings";
import { useAuth } from "./hooks/useAuth";
import { usePatchGeneration } from "./hooks/usePatchGeneration";
import "./App.css";

export default function App() {
  const { theme, toggleTheme } = useTheme();
  const { indexState, indexStatusText, fetchIndex } = useIndex();
  const settings = useSettings();
  const auth = useAuth();
  const patchGen = usePatchGeneration();

  const [showIndexModal, setShowIndexModal] = useState(false);
  const [treeRefreshKey, setTreeRefreshKey] = useState(0);

  useEffect(() => {
    fetchIndex();
    settings.fetchSettings();
  }, [fetchIndex, settings.fetchSettings]);

  return (
    <div className="app">
      <TopBar
        indexState={indexState}
        indexStatusText={indexStatusText}
        theme={theme}
        toggleTheme={toggleTheme}
        onOpenIndexModal={() => setShowIndexModal(true)}
        auth={auth}
        repoName={settings.repoName}
      />

      <main className="layout">
        <InputPanel
          settings={settings}
          patchGen={patchGen}
          isLoggedIn={auth.isLoggedIn}
          isIndexed={indexState === "ready"}
          onLogin={auth.login}
          onOpenIndexModal={() => setShowIndexModal(true)}
        />

        <OutputPanel
          error={patchGen.error}
          setError={patchGen.setError}
          loading={patchGen.loading}
          loadingStep={patchGen.loadingStep}
          refineLoading={patchGen.refineLoading}
          result={patchGen.result}
          showRawJson={patchGen.showRawJson}
          setShowRawJson={patchGen.setShowRawJson}
          treeRefreshKey={treeRefreshKey}
          handleGenerateFix={patchGen.handleGenerateFix}
          feedback={patchGen.feedback}
          setFeedback={patchGen.setFeedback}
          handleRefineFix={patchGen.handleRefineFix}
          hasRepoScope={auth.user?.has_repo_scope ?? false}
          isLoggedIn={auth.isLoggedIn}
          indexState={indexState}
          onLogin={auth.login}
          onOpenIndexModal={() => setShowIndexModal(true)}
          repoName={settings.repoName}
        />
      </main>

      <IndexModal
        open={showIndexModal}
        onClose={() => setShowIndexModal(false)}
        onIndexed={() => {
          fetchIndex();
          setTreeRefreshKey((k) => k + 1);
        }}
      />
    </div>
  );
}

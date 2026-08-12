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
  const patchGen = usePatchGeneration({
    llmProvider: settings.llmProvider,
    modelName: settings.modelName,
    onLlmRequest: settings.fetchSettings,
  });

  const [showIndexModal, setShowIndexModal] = useState(false);
  const [treeRefreshKey, setTreeRefreshKey] = useState(0);

  const handleLogin = () => auth.login(settings.backendUrl);

  useEffect(() => {
    auth.checkAuth();
    fetchIndex();
    settings.fetchSettings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
        onLogin={handleLogin}
      />

      <main className="layout">
        <InputPanel
          settings={settings}
          patchGen={patchGen}
          isLoggedIn={auth.isLoggedIn}
          isIndexed={indexState === "ready"}
          onLogin={handleLogin}
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
          onLogin={handleLogin}
          onOpenIndexModal={() => setShowIndexModal(true)}
          repoName={settings.repoName}
        />
      </main>

      <IndexModal
        open={showIndexModal}
        onClose={() => setShowIndexModal(false)}
        onIndexed={() => {
          fetchIndex();
          settings.fetchSettings();
          setTreeRefreshKey((k) => k + 1);
        }}
        isIndexed={indexState === "ready"}
        repoName={settings.repoName}
      />
    </div>
  );
}

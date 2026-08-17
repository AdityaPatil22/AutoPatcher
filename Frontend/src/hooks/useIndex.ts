import { useCallback, useState } from "react";
import { getIndexStatus } from "../api/indexing";

export function useIndex() {
  const [indexState, setIndexState] = useState<
    "checking" | "ready" | "empty" | "stale" | "error"
  >("checking");
  const [indexChunks, setIndexChunks] = useState(0);

  const fetchIndex = useCallback(async () => {
    try {
      const data = await getIndexStatus();
      if (data.stale) {
        setIndexState("stale");
        setIndexChunks(data.total_chunks);
      } else if (data.indexed && data.total_chunks > 0) {
        setIndexState("ready");
        setIndexChunks(data.total_chunks);
      } else {
        setIndexState("empty");
      }
    } catch {
      setIndexState("error");
    }
  }, []);

  const indexStatusText =
    indexState === "ready"
      ? `Indexed (${indexChunks} chunks)`
      : indexState === "stale"
        ? "Index stale — re-index"
      : indexState === "empty"
        ? "Not indexed"
        : indexState === "error"
          ? "Backend offline"
          : "Checking...";

  return { indexState, indexChunks, indexStatusText, fetchIndex } as const;
}

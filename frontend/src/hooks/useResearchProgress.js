import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../services/api";

const ACTIVE_JOB_STATUSES = new Set(["queued", "running"]);
const ACTIVE_RESEARCH_STATUSES = new Set([
  "queued",
  "planning",
  "searching",
  "evaluating",
  "summarizing",
  "analyzing",
  "critiquing",
  "writing",
]);

const POLL_INTERVAL_MS = 2500;

export function useResearchProgress(researchId, projectStatus) {
  const [progress, setProgress] = useState(null);
  const [polling, setPolling] = useState(false);
  const intervalRef = useRef(null);

  const shouldPoll =
    ACTIVE_JOB_STATUSES.has(progress?.status) ||
    ACTIVE_RESEARCH_STATUSES.has(projectStatus);

  const fetchProgress = useCallback(async () => {
    try {
      const data = await api.getProgress(researchId);
      setProgress(data);
      return data;
    } catch {
      return null;
    }
  }, [researchId]);

  const startPolling = useCallback(() => {
    setPolling(true);
  }, []);

  const stopPolling = useCallback(() => {
    setPolling(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!researchId) return undefined;

    if (shouldPoll || polling) {
      fetchProgress();
      intervalRef.current = setInterval(fetchProgress, POLL_INTERVAL_MS);
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      };
    }

    return undefined;
  }, [researchId, shouldPoll, polling, fetchProgress]);

  useEffect(() => {
    if (progress?.status === "completed" || progress?.status === "failed") {
      stopPolling();
    }
  }, [progress?.status, stopPolling]);

  return {
    progress,
    polling,
    startPolling,
    stopPolling,
    fetchProgress,
    isActive: shouldPoll || polling,
  };
}

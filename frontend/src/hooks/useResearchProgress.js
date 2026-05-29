import { useCallback, useEffect, useRef, useState } from "react";
import { api, subscribeProgressStream } from "../services/api";
import { ACTIVE_JOB_STATUSES, RUNNING_STATUSES } from "../utils/researchConfig";

const POLL_INTERVAL_MS = 2000;
const TERMINAL_STATUSES = new Set(["completed", "failed"]);

export function useResearchProgress(researchId, projectStatus, enabled = true) {
  const [progress, setProgress] = useState(null);
  const [transport, setTransport] = useState("idle");
  const [forcePoll, setForcePoll] = useState(false);
  const intervalRef = useRef(null);
  const streamAbortRef = useRef(null);
  const tabVisibleRef = useRef(true);

  const shouldTrack =
    enabled &&
    (forcePoll ||
      ACTIVE_JOB_STATUSES.has(progress?.status) ||
      RUNNING_STATUSES.has(projectStatus));

  const fetchProgress = useCallback(async () => {
    if (!researchId) return null;
    try {
      const data = await api.getProgress(researchId);
      setProgress(data);
      return data;
    } catch (err) {
      if (err.message?.includes("404") || err.message?.includes("No job")) {
        return null;
      }
      throw err;
    }
  }, [researchId]);

  const stopTracking = useCallback(() => {
    setForcePoll(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (streamAbortRef.current) {
      streamAbortRef.current.abort();
      streamAbortRef.current = null;
    }
    setTransport("idle");
  }, []);

  const startPolling = useCallback(() => {
    setForcePoll(true);
  }, []);

  useEffect(() => {
    const onVisibility = () => {
      tabVisibleRef.current = document.visibilityState === "visible";
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, []);

  useEffect(() => {
    if (!researchId || !shouldTrack) {
      stopTracking();
      return undefined;
    }

    let cancelled = false;

    const pollOnce = async () => {
      if (!tabVisibleRef.current) return;
      try {
        const data = await fetchProgress();
        if (data && TERMINAL_STATUSES.has(data.status)) {
          stopTracking();
        }
      } catch {
        /* 401 handled in api.request */
      }
    };

    const startPollingLoop = () => {
      setTransport("polling");
      pollOnce();
      intervalRef.current = setInterval(pollOnce, POLL_INTERVAL_MS);
    };

    const startStream = () => {
      streamAbortRef.current = new AbortController();
      setTransport("sse");
      subscribeProgressStream(
        researchId,
        (data) => {
          if (cancelled) return;
          setProgress(data);
          if (TERMINAL_STATUSES.has(data.status)) {
            stopTracking();
          }
        },
        streamAbortRef.current.signal,
      ).catch(() => {
        if (!cancelled) {
          startPollingLoop();
        }
      });
    };

    startStream();

    return () => {
      cancelled = true;
      stopTracking();
    };
  }, [researchId, shouldTrack, fetchProgress, stopTracking]);

  useEffect(() => {
    if (progress?.status === "completed" || progress?.status === "failed") {
      stopTracking();
    }
  }, [progress?.status, stopTracking]);

  return {
    progress,
    transport,
    startPolling,
    stopPolling: stopTracking,
    fetchProgress,
    isActive: shouldTrack,
  };
}

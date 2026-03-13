import { formatRunErrorMessage } from "./run-error-message";
import type { Run } from "./types";

const FAST_POLL_INTERVAL_MS = 1500;
const SLOW_POLL_INTERVAL_MS = 5000;
const LONG_TASK_THRESHOLD_MS = 180000;

function sleep(milliseconds: number) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

interface RunArtifactPollingLabels {
  latestLoadedStatus: string;
  initialLoadingStatus: string;
  completedStatus: string;
  syncingStatus: string;
  slowLoadingStatus: string;
  failedStatus: string;
}

interface PollForArtifactOptions<TArtifact> {
  runId?: string;
  loadArtifact: () => Promise<TArtifact>;
  loadRun: (runId: string) => Promise<Run>;
  setArtifact: (artifact: TArtifact) => void;
  setStatus: (status: string) => void;
  labels: RunArtifactPollingLabels;
  isCancelled: () => boolean;
}

export async function loadArtifactWithPolling<TArtifact>({
  runId,
  loadArtifact,
  loadRun,
  setArtifact,
  setStatus,
  labels,
  isCancelled,
}: PollForArtifactOptions<TArtifact>) {
  if (!runId) {
    const artifact = await loadArtifact();
    if (isCancelled()) {
      return;
    }

    setArtifact(artifact);
    setStatus(labels.latestLoadedStatus);
    return;
  }

  setStatus(labels.initialLoadingStatus);

  const startedAt = Date.now();
  let slowPolling = false;

  while (!isCancelled()) {
    const run = await loadRun(runId);

    if (run.status === "completed") {
      try {
        const artifact = await loadArtifact();
        if (isCancelled()) {
          return;
        }

        setArtifact(artifact);
        setStatus(labels.completedStatus);
        return;
      } catch {
        if (!isCancelled()) {
          setStatus(labels.syncingStatus);
        }
      }
    }

    if (run.status === "failed") {
      throw new Error(formatRunErrorMessage(run.error_message, labels.failedStatus));
    }

    if (!slowPolling && Date.now() - startedAt >= LONG_TASK_THRESHOLD_MS) {
      slowPolling = true;
      if (!isCancelled()) {
        setStatus(labels.slowLoadingStatus);
      }
    }

    await sleep(slowPolling ? SLOW_POLL_INTERVAL_MS : FAST_POLL_INTERVAL_MS);
  }
}
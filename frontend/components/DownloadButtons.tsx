"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@thomasbrunner-spec/design-system";
import type {
  JobStatus,
  OfferJobCreateResponse,
  OfferRenderJobStatusResponse,
} from "@/lib/types/offer";

type Format = "pptx" | "word";

interface DownloadButtonsProps {
  offerId: string;
}

const POLL_INTERVAL_MS = 2000;

interface RenderJob {
  jobId: string;
  format: Format;
}

export function DownloadButtons({ offerId }: DownloadButtonsProps) {
  const [job, setJob] = useState<RenderJob | null>(null);
  const [phase, setPhase] = useState<JobStatus | "idle">("idle");
  const [elapsedSec, setElapsedSec] = useState(0);
  const [error, setError] = useState<string | null>(null);
  // Latest format the user clicked — used to label the spinner and as
  // a stable handle for "which button is pending" after the click event
  // has been long forgotten.
  const pendingFormat = job?.format ?? null;
  const loading = phase === "queued" || phase === "running";
  // Avoid double-firing the download anchor if React re-renders.
  const downloadFiredRef = useRef<string | null>(null);

  // Elapsed counter — render runs 2-5 min, so an honest tick keeps the user
  // from refreshing.
  useEffect(() => {
    if (!loading) {
      setElapsedSec(0);
      return;
    }
    const startedAt = Date.now();
    const tick = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    return () => clearInterval(tick);
  }, [loading]);

  // Poll the job until terminal status; on complete, trigger the download
  // via an anchor click. window.open() doesn't work here — the user gesture
  // is gone after the multi-minute wait — but a synthetic anchor click with
  // the `download` attribute bypasses the popup blocker.
  useEffect(() => {
    if (!job) return;
    let cancelled = false;

    async function poll() {
      while (!cancelled && job) {
        try {
          const response = await fetch(`/api/offers/render/jobs/${job.jobId}`, {
            cache: "no-store",
          });
          if (!response.ok) {
            const data = await response.json().catch(() => null);
            throw new Error(
              data?.error ?? `Status-Polling fehlgeschlagen (${response.status})`,
            );
          }
          const data = (await response.json()) as OfferRenderJobStatusResponse;
          if (cancelled) return;
          setPhase(data.status);

          if (data.status === "complete" && data.result) {
            triggerDownload(job.jobId, job.format, data.result);
            return;
          }
          if (data.status === "failed") {
            setError(data.error ?? "Unbekannter Render-Fehler");
            return;
          }
          if (data.status === "not_found") {
            setError("Render-Job nicht gefunden — bitte erneut anfordern.");
            return;
          }
        } catch (err) {
          if (cancelled) return;
          setError(err instanceof Error ? err.message : "Unknown error");
          setPhase("failed");
          return;
        }
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
      }
    }

    poll();
    return () => {
      cancelled = true;
    };
  }, [job]);

  const triggerDownload = (
    jobId: string,
    format: Format,
    result: OfferRenderJobStatusResponse["result"],
  ) => {
    if (!result) return;
    if (downloadFiredRef.current === jobId) return;
    downloadFiredRef.current = jobId;
    const url = format === "pptx" ? result.pptx_url : result.word_url;
    if (!url) {
      setError(`${format.toUpperCase()}-URL fehlt in der Antwort.`);
      return;
    }
    const ext = format === "pptx" ? "pptx" : "docx";
    const a = document.createElement("a");
    a.href = url;
    a.download = `${result.filename_prefix}.${ext}`;
    a.rel = "noopener noreferrer";
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const startRender = async (format: Format, force = false) => {
    setError(null);
    setJob(null);
    setPhase("queued");
    downloadFiredRef.current = null;
    try {
      const qs = new URLSearchParams({ format });
      if (force) qs.set("force", "true");
      const response = await fetch(
        `/api/offers/${offerId}/render?${qs.toString()}`,
        { method: "POST" },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.error ?? `Render-Enqueue fehlgeschlagen (${response.status})`);
      }
      const created = data as OfferJobCreateResponse;
      setJob({ jobId: created.job_id, format });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setPhase("failed");
    }
  };

  const phaseLabel =
    phase === "queued"
      ? "In Warteschlange…"
      : phase === "running"
        ? `Render läuft (${elapsedSec}s, typisch 2–5 Min)…`
        : phase === "complete"
          ? "Fertig — Download wird gestartet."
          : null;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        <Button
          variant="primary"
          onClick={() => startRender("pptx")}
          disabled={loading}
        >
          {pendingFormat === "pptx" && loading ? "Rendere…" : "PowerPoint herunterladen"}
        </Button>
        <Button
          variant="secondary"
          onClick={() => startRender("word")}
          disabled={loading}
        >
          {pendingFormat === "word" && loading ? "Rendere…" : "Word herunterladen"}
        </Button>
        <button
          type="button"
          onClick={() => startRender("pptx", true)}
          disabled={loading}
          className="text-xs text-text-muted underline underline-offset-2 hover:text-text-dim disabled:opacity-50"
          title="Cache ignorieren und mit der aktuellen Skill-Version neu erzeugen"
        >
          ↻ Neu rendern (Skill-Iteration)
        </button>
      </div>
      <p className="text-xs text-text-muted">
        Render läuft asynchron im Worker. Folge-Aufrufe sind aus dem Cache und sofort.
      </p>
      {phaseLabel && (
        <p className="text-xs text-text-dim" role="status" aria-live="polite">
          {phaseLabel}
        </p>
      )}
      {error && (
        <p className="text-xs text-danger" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { Button } from "@thomasbrunner-spec/design-system";
import type { OfferRenderResponse } from "@/lib/types/offer";

type Format = "pptx" | "word";

interface DownloadButtonsProps {
  offerId: string;
}

export function DownloadButtons({ offerId }: DownloadButtonsProps) {
  const [pending, setPending] = useState<Format | null>(null);
  const [error, setError] = useState<string | null>(null);

  const triggerDownload = async (format: Format) => {
    setPending(format);
    setError(null);
    try {
      const response = await fetch(
        `/api/offers/${offerId}/render?format=${format}`,
        { method: "POST" }
      );
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.error ?? `Render failed: ${response.status}`);
      }
      const data: OfferRenderResponse = await response.json();
      const url = format === "pptx" ? data.pptx_url : data.word_url;
      if (!url) {
        throw new Error(`${format.toUpperCase()}-URL fehlt in der Antwort.`);
      }
      // window.open() after a multi-minute await is silently blocked by the
      // browser's popup blocker (the user-gesture is gone). A programmatic
      // anchor click with `download` attribute is treated as a normal
      // download and goes through.
      const ext = format === "pptx" ? "pptx" : "docx";
      const a = document.createElement("a");
      a.href = url;
      a.download = `${data.filename_prefix}.${ext}`;
      a.rel = "noopener noreferrer";
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setPending(null);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        <Button
          variant="primary"
          onClick={() => triggerDownload("pptx")}
          disabled={pending !== null}
        >
          {pending === "pptx" ? "Rendere…" : "PowerPoint herunterladen"}
        </Button>
        <Button
          variant="secondary"
          onClick={() => triggerDownload("word")}
          disabled={pending !== null}
        >
          {pending === "word" ? "Rendere…" : "Word herunterladen"}
        </Button>
      </div>
      <p className="text-xs text-text-muted">
        Erstmaliger Render dauert 2–5 Minuten (Anthropic Code-Execution).
        Folge-Aufrufe sind aus dem Cache und sofort.
      </p>
      {error && (
        <p className="text-xs text-danger" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

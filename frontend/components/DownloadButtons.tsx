"use client";

import { useState } from "react";
import { Button } from "@thomasbrunner-spec/design-system";
import type { OfferRenderResponse } from "@/lib/types/offer";

type Format = "pptx" | "word";

interface DownloadButtonsProps {
  offerId: string;
  hasWordRenderer?: boolean;
}

export function DownloadButtons({
  offerId,
  hasWordRenderer = false,
}: DownloadButtonsProps) {
  const [pending, setPending] = useState<Format | null>(null);
  const [error, setError] = useState<string | null>(null);

  const triggerDownload = async (format: Format) => {
    setPending(format);
    setError(null);
    try {
      const response = await fetch(`/api/offers/${offerId}/render`, {
        method: "POST",
      });
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.error ?? `Render failed: ${response.status}`);
      }
      const data: OfferRenderResponse = await response.json();
      const url = format === "pptx" ? data.pptx_url : data.word_url;
      if (!url) {
        throw new Error(
          format === "word"
            ? "Word-Renderer noch nicht verfügbar."
            : "PPT-URL fehlt."
        );
      }
      window.open(url, "_blank", "noopener,noreferrer");
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
        {hasWordRenderer && (
          <Button
            variant="secondary"
            onClick={() => triggerDownload("word")}
            disabled={pending !== null}
          >
            {pending === "word" ? "Rendere…" : "Word herunterladen"}
          </Button>
        )}
      </div>
      {error && (
        <p className="text-xs text-danger" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

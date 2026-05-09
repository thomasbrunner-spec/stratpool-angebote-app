"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import {
  OFFER_STATUS_LABELS,
  type OfferStatus,
} from "@/lib/types/offer";

const STATUS_ORDER: OfferStatus[] = ["draft", "sent", "won", "lost"];

interface StatusSelectorProps {
  offerId: string;
  initialStatus: OfferStatus;
}

export function StatusSelector({ offerId, initialStatus }: StatusSelectorProps) {
  const [status, setStatus] = useState<OfferStatus>(initialStatus);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  const handleChange = async (next: OfferStatus) => {
    if (next === status) return;
    const previous = status;
    setStatus(next);
    setError(null);

    try {
      const response = await fetch(`/api/offers/${offerId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: next }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.error ?? `Request failed: ${response.status}`);
      }
      // Refresh server data so the list and details reflect the new status.
      startTransition(() => router.refresh());
    } catch (err) {
      setStatus(previous);
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  return (
    <div className="space-y-2">
      <label htmlFor="offer-status" className="text-xs uppercase tracking-wider text-text-muted">
        Status
      </label>
      <select
        id="offer-status"
        value={status}
        onChange={(e) => handleChange(e.target.value as OfferStatus)}
        disabled={isPending}
        className="h-10 rounded-md border border-slate/30 bg-ink/40 px-3 text-sm text-text outline-none transition focus:border-signal focus:ring-1 focus:ring-signal disabled:opacity-50"
      >
        {STATUS_ORDER.map((s) => (
          <option key={s} value={s}>
            {OFFER_STATUS_LABELS[s]}
          </option>
        ))}
      </select>
      {error && (
        <p className="text-xs text-danger" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

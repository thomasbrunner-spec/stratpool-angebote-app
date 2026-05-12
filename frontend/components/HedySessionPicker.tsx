"use client";

import { useEffect, useRef, useState } from "react";
import { Button, Input } from "@thomasbrunner-spec/design-system";
import type {
  HedySessionDetail,
  HedySessionList,
  HedySessionListItem,
} from "@/lib/types/hedy";

interface HedySessionPickerProps {
  open: boolean;
  onClose: () => void;
  onSelect: (detail: HedySessionDetail) => void;
}

const PAGE_SIZE = 20;
const SEARCH_DEBOUNCE_MS = 300;

const dateFormatter = new Intl.DateTimeFormat("de-DE", {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatStart(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : dateFormatter.format(d);
}

function formatDuration(min: number | null): string | null {
  if (min === null || min === undefined) return null;
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m === 0 ? `${h} h` : `${h} h ${m} min`;
}

export function HedySessionPicker({ open, onClose, onSelect }: HedySessionPickerProps) {
  const [items, setItems] = useState<HedySessionListItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectingId, setSelectingId] = useState<string | null>(null);

  // Reset list state whenever the modal opens or the search term changes.
  useEffect(() => {
    if (!open) return;
    const handle = setTimeout(() => {
      setAppliedSearch(search.trim());
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [open, search]);

  const requestIdRef = useRef(0);

  useEffect(() => {
    if (!open) return;
    setItems([]);
    setCursor(null);
    setHasMore(false);
    setError(null);
    setLoading(true);

    const myRequest = ++requestIdRef.current;
    const params = new URLSearchParams({ limit: String(PAGE_SIZE) });
    if (appliedSearch) params.set("q", appliedSearch);
    fetch(`/api/hedy/sessions?${params.toString()}`, { cache: "no-store" })
      .then(async (r) => {
        if (!r.ok) {
          const data = await r.json().catch(() => null);
          throw new Error(data?.error ?? `Sessions konnten nicht geladen werden (${r.status})`);
        }
        return r.json() as Promise<HedySessionList>;
      })
      .then((data) => {
        if (myRequest !== requestIdRef.current) return;
        setItems(data.items);
        setCursor(data.nextCursor);
        setHasMore(data.hasMore);
      })
      .catch((err) => {
        if (myRequest !== requestIdRef.current) return;
        setError(err instanceof Error ? err.message : "Unknown error");
      })
      .finally(() => {
        if (myRequest !== requestIdRef.current) return;
        setLoading(false);
      });
  }, [open, appliedSearch]);

  // Lock body scroll while the dialog is up.
  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  // ESC closes — only when no selection is in flight (would re-open mid-fetch otherwise).
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !selectingId) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, selectingId, onClose]);

  const loadMore = async () => {
    if (!cursor || loadingMore) return;
    setLoadingMore(true);
    setError(null);
    const params = new URLSearchParams({ limit: String(PAGE_SIZE), after: cursor });
    if (appliedSearch) params.set("q", appliedSearch);
    try {
      const r = await fetch(`/api/hedy/sessions?${params.toString()}`, { cache: "no-store" });
      if (!r.ok) {
        const data = await r.json().catch(() => null);
        throw new Error(data?.error ?? `Sessions konnten nicht nachgeladen werden (${r.status})`);
      }
      const data = (await r.json()) as HedySessionList;
      setItems((prev) => [...prev, ...data.items]);
      setCursor(data.nextCursor);
      setHasMore(data.hasMore);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoadingMore(false);
    }
  };

  const handleSelect = async (sessionId: string) => {
    setSelectingId(sessionId);
    setError(null);
    try {
      const r = await fetch(`/api/hedy/sessions/${encodeURIComponent(sessionId)}`, {
        cache: "no-store",
      });
      if (!r.ok) {
        const data = await r.json().catch(() => null);
        throw new Error(data?.error ?? `Session konnte nicht geladen werden (${r.status})`);
      }
      const detail = (await r.json()) as HedySessionDetail;
      if (!detail.transcript || detail.transcript.trim().length < 50) {
        throw new Error(
          "Diese Session hat noch kein verwendbares Transkript (mindestens 50 Zeichen).",
        );
      }
      onSelect(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setSelectingId(null);
    }
  };

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="hedy-picker-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && !selectingId) onClose();
      }}
    >
      <div className="flex max-h-[85vh] w-full max-w-2xl flex-col rounded-lg border border-slate/30 bg-ink shadow-xl">
        <div className="flex items-center justify-between border-b border-slate/30 px-5 py-4">
          <div>
            <h2 id="hedy-picker-title" className="font-display text-lg font-semibold text-text">
              Hedy-Session auswählen
            </h2>
            <p className="text-xs text-text-dim">
              Wähle einen Discovery-Call aus — Transkript und Notizen werden ins Formular
              übernommen.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={!!selectingId}
            className="rounded-md p-1 text-text-dim transition hover:text-text disabled:opacity-50"
            aria-label="Schließen"
          >
            ✕
          </button>
        </div>

        <div className="border-b border-slate/30 px-5 py-3">
          <Input
            type="search"
            placeholder="Nach Titel suchen (z. B. Kundenname)…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            disabled={!!selectingId}
          />
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading && (
            <p className="px-5 py-8 text-center text-sm text-text-dim">Lade Sessions…</p>
          )}
          {!loading && error && (
            <p className="px-5 py-4 text-sm text-danger" role="alert">
              {error}
            </p>
          )}
          {!loading && !error && items.length === 0 && (
            <p className="px-5 py-8 text-center text-sm text-text-dim">
              {appliedSearch
                ? `Keine Session mit „${appliedSearch}" im Titel gefunden.`
                : "Keine Sessions verfügbar."}
            </p>
          )}
          {!loading && items.length > 0 && (
            <ul className="divide-y divide-slate/20">
              {items.map((item) => {
                const isSelecting = selectingId === item.sessionId;
                const duration = formatDuration(item.durationMinutes);
                return (
                  <li key={item.sessionId}>
                    <button
                      type="button"
                      onClick={() => handleSelect(item.sessionId)}
                      disabled={!!selectingId}
                      className="flex w-full items-start justify-between gap-4 px-5 py-3 text-left transition hover:bg-ink/60 disabled:opacity-50"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-text">{item.title}</p>
                        <p className="text-xs text-text-dim">
                          {formatStart(item.startTime)}
                          {duration ? ` · ${duration}` : ""}
                        </p>
                      </div>
                      {isSelecting && (
                        <span className="shrink-0 text-xs text-text-dim">Lade Transkript…</span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-slate/30 px-5 py-3">
          <span className="text-xs text-text-muted">
            {items.length > 0 ? `${items.length} Session${items.length === 1 ? "" : "s"}` : ""}
          </span>
          <div className="flex items-center gap-2">
            {hasMore && cursor && (
              <Button
                type="button"
                variant="secondary"
                onClick={loadMore}
                disabled={loadingMore || !!selectingId}
              >
                {loadingMore ? "Lade…" : "Mehr laden"}
              </Button>
            )}
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              disabled={!!selectingId}
            >
              Abbrechen
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

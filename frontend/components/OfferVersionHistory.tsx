import Link from "next/link";
import { Card } from "@thomasbrunner-spec/design-system";
import type { OfferVersionSummary } from "@/lib/types/offer";

const DATE_FORMAT = new Intl.DateTimeFormat("de-DE", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

interface OfferVersionHistoryProps {
  offerId: string;
  versions: OfferVersionSummary[];
}

export function OfferVersionHistory({ offerId, versions }: OfferVersionHistoryProps) {
  if (versions.length <= 1) {
    return null;
  }

  return (
    <Card>
      <Card.Header>
        <Card.Title>Versionsverlauf</Card.Title>
        <Card.Description>
          {versions.length} Versionen — die aktuelle wird oben auf der Detailseite gezeigt.
        </Card.Description>
      </Card.Header>
      <Card.Content className="space-y-3">
        {versions.map((v) => (
          <div
            key={v.id}
            className="flex flex-wrap items-baseline justify-between gap-3 border-b border-border/40 pb-3 last:border-b-0 last:pb-0"
          >
            <div className="space-y-1">
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-sm text-signal">v{v.version_number}</span>
                {v.is_current && (
                  <span className="font-mono text-xs uppercase tracking-wider text-text-muted">
                    aktuell
                  </span>
                )}
                <span className="text-xs text-text-dim">
                  {DATE_FORMAT.format(new Date(v.created_at))}
                </span>
              </div>
              {v.revision_notes && (
                <p className="text-sm text-text-dim leading-relaxed max-w-2xl">
                  {v.revision_notes}
                </p>
              )}
            </div>
            {!v.is_current && (
              <Link
                href={`/angebote/${offerId}/versions/${v.version_number}`}
                className="font-mono text-xs text-signal hover:underline"
              >
                ansehen →
              </Link>
            )}
          </div>
        ))}
      </Card.Content>
    </Card>
  );
}

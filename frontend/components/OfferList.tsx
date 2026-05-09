import Link from "next/link";
import { Card } from "@thomasbrunner-spec/design-system";
import {
  CONSULTING_TYPE_LABELS,
  type OfferListItem,
} from "@/lib/types/offer";
import { StatusBadge } from "./StatusBadge";

const DATE_FORMAT = new Intl.DateTimeFormat("de-DE", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

const PRICE_FORMAT = new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

function formatPrice(price: OfferListItem["price_eur"]): string {
  if (price === null || price === undefined) return "—";
  const num = typeof price === "string" ? Number.parseFloat(price) : price;
  return Number.isFinite(num) ? PRICE_FORMAT.format(num) : "—";
}

export function OfferList({ offers }: { offers: OfferListItem[] }) {
  if (offers.length === 0) {
    return (
      <Card>
        <Card.Content className="py-12 text-center text-text-dim">
          Noch keine Angebote vorhanden.{" "}
          <Link href="/angebote/neu" className="text-signal hover:underline">
            Erstes Angebot generieren
          </Link>
          .
        </Card.Content>
      </Card>
    );
  }

  return (
    <Card>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-slate/30 text-left text-xs uppercase tracking-wider text-text-muted">
            <tr>
              <th className="px-4 py-3 font-medium">Kunde</th>
              <th className="px-4 py-3 font-medium">Beratungsart</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium text-right">Investition</th>
              <th className="px-4 py-3 font-medium">Datum</th>
              <th className="px-4 py-3 font-medium text-right">Version</th>
            </tr>
          </thead>
          <tbody>
            {offers.map((o) => (
              <tr
                key={o.id}
                className="border-b border-slate/15 transition hover:bg-surface/40"
              >
                <td className="px-4 py-3">
                  <Link
                    href={`/angebote/${o.id}`}
                    className="font-medium text-text hover:text-signal"
                  >
                    {o.client_name}
                  </Link>
                  {o.industry && (
                    <div className="text-xs text-text-muted">{o.industry}</div>
                  )}
                </td>
                <td className="px-4 py-3 text-text-dim">
                  {CONSULTING_TYPE_LABELS[o.consulting_type]}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={o.status} />
                </td>
                <td className="px-4 py-3 text-right font-mono text-text-dim">
                  {formatPrice(o.price_eur)}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-text-muted">
                  {DATE_FORMAT.format(new Date(o.created_at))}
                </td>
                <td className="px-4 py-3 text-right font-mono text-xs text-text-muted">
                  v{o.latest_version_number}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

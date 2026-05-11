import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { Card, Header } from "@thomasbrunner-spec/design-system";
import { apiCall } from "@/lib/api";
import { createClient } from "@/lib/supabase/server";
import { LogoutButton } from "@/components/LogoutButton";
import { OfferContentSection } from "@/components/OfferContentSection";
import { OfferVersionHistory } from "@/components/OfferVersionHistory";
import { StatusBadge } from "@/components/StatusBadge";
import { StatusSelector } from "@/components/StatusSelector";
import { DownloadButtons } from "@/components/DownloadButtons";
import {
  CONSULTING_TYPE_LABELS,
  type OfferDetail,
  type OfferVersionSummary,
} from "@/lib/types/offer";

const DATE_FORMAT = new Intl.DateTimeFormat("de-DE", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const PRICE_FORMAT = new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

function formatPrice(price: OfferDetail["price_eur"]): string {
  if (price === null || price === undefined) return "—";
  const num = typeof price === "string" ? Number.parseFloat(price) : price;
  return Number.isFinite(num) ? PRICE_FORMAT.format(num) : "—";
}

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function AngebotDetailPage({ params }: PageProps) {
  const { id } = await params;

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  let offer: OfferDetail;
  let versions: OfferVersionSummary[] = [];
  try {
    [offer, versions] = await Promise.all([
      apiCall<OfferDetail>(`/api/v1/offers/${id}`),
      apiCall<OfferVersionSummary[]>(`/api/v1/offers/${id}/versions`),
    ]);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    // 410 = legacy few-shot-pool entry, not user-facing content.
    if (message.includes("404") || message.includes("410")) {
      notFound();
    }
    throw err;
  }

  return (
    <>
      <Header
        appName="Angebote"
        rightSlot={
          <>
            <Link href="/angebote" className="text-xs text-text-dim hover:text-text">
              Liste
            </Link>
            <span className="font-mono text-xs text-text-dim hidden sm:inline">
              {user.email}
            </span>
            <LogoutButton />
          </>
        }
      />

      <main className="container mx-auto max-w-4xl space-y-8 px-6 py-12">
        <div className="space-y-2">
          <Link
            href="/angebote"
            className="font-mono text-xs text-text-muted hover:text-signal"
          >
            ← zurück zur Liste
          </Link>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-1">
              <h1 className="font-display text-3xl font-semibold tracking-tight">
                {offer.content.angebot_titel}
              </h1>
              <p className="text-text-dim">
                Für <span className="text-text">{offer.client_name}</span>
                {offer.industry && (
                  <span className="text-text-muted"> · {offer.industry}</span>
                )}
              </p>
            </div>
            <StatusBadge status={offer.status} />
          </div>
        </div>

        <Card>
          <Card.Header>
            <Card.Title>Angebot-Daten</Card.Title>
          </Card.Header>
          <Card.Content className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <Meta label="Beratungsart" value={CONSULTING_TYPE_LABELS[offer.consulting_type]} />
            <Meta label="Investition" value={formatPrice(offer.price_eur)} />
            <Meta label="Erstellt" value={DATE_FORMAT.format(new Date(offer.created_at))} />
            <Meta label="Version" value={`v${offer.version_number}`} />
            <Meta
              label="Version erstellt"
              value={DATE_FORMAT.format(new Date(offer.version_created_at))}
            />
            <Meta label="Co-Berater" value={offer.co_consultant_name ?? "—"} />
            <StatusSelector offerId={offer.id} initialStatus={offer.status} />
          </Card.Content>
          <Card.Footer>
            <DownloadButtons offerId={offer.id} />
          </Card.Footer>
        </Card>

        <OfferContentSection offerId={offer.id} content={offer.content} />

        <OfferVersionHistory offerId={offer.id} versions={versions} />
      </main>
    </>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1">
      <div className="text-xs uppercase tracking-wider text-text-muted">{label}</div>
      <div className="text-sm text-text">{value}</div>
    </div>
  );
}

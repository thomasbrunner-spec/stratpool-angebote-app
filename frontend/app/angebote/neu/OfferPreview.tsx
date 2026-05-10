import { Badge, Card } from "@thomasbrunner-spec/design-system";
import { DownloadButtons } from "@/components/DownloadButtons";
import { OfferContentView } from "@/components/OfferContentView";
import type { OfferGenerateResponse } from "@/lib/types/offer";

interface OfferPreviewProps {
  result: OfferGenerateResponse;
}

export function OfferPreview({ result }: OfferPreviewProps) {
  const c = result.content;
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h2 className="font-display text-2xl font-semibold tracking-tight">
            {c.angebot_titel}
          </h2>
          <p className="text-text-dim">
            Für <span className="text-text">{c.client_name}</span>
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <Badge variant="success">DRAFT v{result.version_number}</Badge>
          <span className="font-mono text-xs text-text-muted">
            {result.retrieved_offer_ids.length} Few-Shots
          </span>
        </div>
      </div>

      <Card>
        <Card.Header>
          <Card.Title>Word / PowerPoint rendern</Card.Title>
          <Card.Description>
            Direkt aus dieser Vorschau heraus, kein Umweg über die Detailseite nötig.
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <DownloadButtons offerId={result.offer_id} />
        </Card.Content>
      </Card>

      <OfferContentView content={c} />

      <Meta result={result} />
    </div>
  );
}

function Meta({ result }: { result: OfferGenerateResponse }) {
  return (
    <Card>
      <Card.Header>
        <Card.Title>Metadaten</Card.Title>
        <Card.Description>Persistiert in Supabase als Offer + OfferVersion v1.</Card.Description>
      </Card.Header>
      <Card.Content className="grid grid-cols-1 gap-3 font-mono text-xs sm:grid-cols-2">
        <MetaRow label="offer_id" value={result.offer_id} />
        <MetaRow label="version_id" value={result.version_id} />
        <MetaRow label="created_at" value={result.created_at} />
        <MetaRow
          label="few_shot_offer_ids"
          value={result.retrieved_offer_ids.join(", ") || "—"}
        />
      </Card.Content>
    </Card>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-text-muted">{label}</span>
      <span className="truncate text-text-dim">{value}</span>
    </div>
  );
}

import { Badge, Card } from "@thomasbrunner-spec/design-system";
import type { OfferContent, OfferGenerateResponse } from "@/lib/types/offer";

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

      <Section title="Ausgangssituation" body={c.ausgangssituation} />
      <Section title="Leistungsumfang" body={c.leistungsumfang_intro} />

      <Card>
        <Card.Header>
          <Card.Title>Bestandteile</Card.Title>
          <Card.Description>{c.bestandteile.length} Pakete</Card.Description>
        </Card.Header>
        <Card.Content className="space-y-5">
          {c.bestandteile.map((b, i) => (
            <Bestandteil key={i} index={i + 1} titel={b.titel} beschreibung={b.beschreibung} />
          ))}
        </Card.Content>
      </Card>

      <Section title="Leistungserbringung" body={c.leistungserbringung} />
      <Section title="Investition" body={c.investition} />
      <Section title="Rahmenbedingungen" body={c.rahmenbedingungen} />

      <Meta result={result} />
    </div>
  );
}

function Section({ title, body }: { title: string; body: string }) {
  return (
    <Card>
      <Card.Header>
        <Card.Title>{title}</Card.Title>
      </Card.Header>
      <Card.Content>
        <p className="whitespace-pre-line leading-relaxed text-text">{body}</p>
      </Card.Content>
    </Card>
  );
}

function Bestandteil({
  index,
  titel,
  beschreibung,
}: {
  index: number;
  titel: string;
  beschreibung: string;
}) {
  return (
    <div className="space-y-2 border-l-2 border-signal/40 pl-4">
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-xs text-signal">#{index}</span>
        <h4 className="font-display text-lg font-semibold">{titel}</h4>
      </div>
      <p className="whitespace-pre-line leading-relaxed text-text-dim">{beschreibung}</p>
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

export type { OfferContent };

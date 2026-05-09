import { Card } from "@thomasbrunner-spec/design-system";
import type { OfferContent } from "@/lib/types/offer";

export function OfferContentView({ content }: { content: OfferContent }) {
  return (
    <div className="space-y-6">
      <Section title="Ausgangssituation" body={content.ausgangssituation} />
      <Section title="Leistungsumfang" body={content.leistungsumfang_intro} />

      <Card>
        <Card.Header>
          <Card.Title>Bestandteile</Card.Title>
          <Card.Description>{content.bestandteile.length} Pakete</Card.Description>
        </Card.Header>
        <Card.Content className="space-y-5">
          {content.bestandteile.map((b, i) => (
            <Bestandteil
              key={i}
              index={i + 1}
              titel={b.titel}
              beschreibung={b.beschreibung}
            />
          ))}
        </Card.Content>
      </Card>

      <Section title="Leistungserbringung" body={content.leistungserbringung} />
      <Section title="Investition" body={content.investition} />
      <Section title="Rahmenbedingungen" body={content.rahmenbedingungen} />
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

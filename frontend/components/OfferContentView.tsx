import { Card } from "@thomasbrunner-spec/design-system";
import type { OfferContent } from "@/lib/types/offer";

export function OfferContentView({ content }: { content: OfferContent }) {
  const c = content;
  return (
    <div className="space-y-6">
      <Card>
        <Card.Header>
          <Card.Title>Management Summary</Card.Title>
        </Card.Header>
        <Card.Content>
          <p className="whitespace-pre-line leading-relaxed text-text">{c.management_summary}</p>
        </Card.Content>
      </Card>

      {c.hook_quote && (
        <blockquote className="border-l-4 border-signal pl-6 py-2 font-display text-xl italic leading-snug text-text">
          „{c.hook_quote}"
        </blockquote>
      )}

      {c.warum_jetzt_argumente?.length > 0 && (
        <Section title="Warum jetzt">
          <ul className="space-y-2 list-disc pl-6 text-text">
            {c.warum_jetzt_argumente.map((arg, i) => (
              <li key={i} className="leading-relaxed">{arg}</li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Ausgangssituation" body={c.ausgangssituation} />

      {c.erkannte_anwendungsfaelle?.length > 0 && (
        <Section title="Erkannte Anwendungsfälle">
          <ul className="space-y-2 list-disc pl-6 text-text">
            {c.erkannte_anwendungsfaelle.map((uc, i) => (
              <li key={i} className="leading-relaxed">{uc}</li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Zielsetzung & Ergebnis" body={c.zielsetzung_und_ergebnis} />

      <Card>
        <Card.Header>
          <Card.Title>Vorgehen in {c.phasen.length} Phasen</Card.Title>
        </Card.Header>
        <Card.Content className="space-y-6">
          {c.phasen.map((p, i) => (
            <PhaseBlock key={i} phase={p} />
          ))}
        </Card.Content>
      </Card>

      {c.technische_basis?.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>Technische Basis</Card.Title>
            <Card.Description>
              {c.technische_basis.length} Optionen — die richtige folgt dem Anwendungsfall.
            </Card.Description>
          </Card.Header>
          <Card.Content className="grid gap-4 md:grid-cols-2">
            {c.technische_basis.map((t, i) => (
              <div key={i} className="space-y-1">
                <div className="font-display text-base font-semibold text-text">{t.titel}</div>
                <p className="text-sm text-text-dim leading-relaxed">{t.beschreibung}</p>
              </div>
            ))}
          </Card.Content>
        </Card>
      )}

      {c.mehrwert_3_ebenen?.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>Mehrwert auf drei Ebenen</Card.Title>
          </Card.Header>
          <Card.Content className="grid gap-4 md:grid-cols-3">
            {c.mehrwert_3_ebenen.map((m, i) => (
              <div key={i} className="space-y-2">
                <div className="font-mono text-xs uppercase tracking-wider text-signal">{m.ebene}</div>
                <ul className="space-y-1 list-disc pl-5 text-sm text-text">
                  {m.punkte.map((p, j) => (
                    <li key={j} className="leading-relaxed">{p}</li>
                  ))}
                </ul>
              </div>
            ))}
          </Card.Content>
        </Card>
      )}

      {c.leistungsumfang_items?.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>Was im Angebot enthalten ist</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            {c.leistungsumfang_items.map((it) => (
              <div key={it.nummer} className="flex gap-4">
                <div className="font-mono text-sm text-signal shrink-0 w-6">{it.nummer}.</div>
                <div className="space-y-1">
                  <div className="font-display text-base font-semibold text-text">{it.titel}</div>
                  <p className="text-sm text-text-dim leading-relaxed">{it.beschreibung}</p>
                </div>
              </div>
            ))}
          </Card.Content>
        </Card>
      )}

      <Section title="Investition" body={c.investition} />
      <Section title="Nächste Schritte" body={c.naechste_schritte} />
    </div>
  );
}

function Section({ title, body, children }: { title: string; body?: string; children?: React.ReactNode }) {
  return (
    <Card>
      <Card.Header>
        <Card.Title>{title}</Card.Title>
      </Card.Header>
      <Card.Content>
        {body ? (
          <p className="whitespace-pre-line leading-relaxed text-text">{body}</p>
        ) : (
          children
        )}
      </Card.Content>
    </Card>
  );
}

function PhaseBlock({ phase }: { phase: OfferContent["phasen"][number] }) {
  const meta = [
    phase.dauer && ["Dauer", phase.dauer],
    phase.format && ["Format", phase.format],
    phase.teilnehmer && ["Teilnehmer", phase.teilnehmer],
    phase.moderation && ["Moderation", phase.moderation],
  ].filter(Boolean) as [string, string][];

  return (
    <div className="space-y-2 border-l-2 border-signal/40 pl-4">
      <div className="flex items-baseline gap-3">
        <span className="font-mono text-xs text-signal">Phase {phase.nummer}</span>
        <h4 className="font-display text-lg font-semibold text-text">{phase.titel}</h4>
      </div>
      {phase.untertitel && (
        <p className="text-sm text-text-muted">{phase.untertitel}</p>
      )}
      <p className="leading-relaxed text-text-dim">{phase.beschreibung}</p>
      {meta.length > 0 && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs text-text-muted">
          {meta.map(([k, v]) => (
            <span key={k}><span className="uppercase">{k}:</span> {v}</span>
          ))}
        </div>
      )}
      {phase.aktivitaeten.length > 0 && (
        <ul className="space-y-1 list-disc pl-5 text-sm text-text">
          {phase.aktivitaeten.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      )}
      <div className="text-sm">
        <span className="font-mono text-xs uppercase text-text-muted">Ergebnis: </span>
        <span className="text-text">{phase.ergebnis}</span>
      </div>
    </div>
  );
}

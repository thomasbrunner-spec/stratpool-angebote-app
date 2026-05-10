"use client";

import { useRef, useState } from "react";
import { Button, Card, Input, Label } from "@thomasbrunner-spec/design-system";
import {
  CONSULTING_TYPE_LABELS,
  type ConsultingType,
  type OfferGenerateRequest,
  type OfferGenerateResponse,
} from "@/lib/types/offer";
import type { Consultant } from "@/lib/types/consultant";
import {
  CoConsultantSelector,
  EMPTY_CO_CONSULTANT,
  type CoConsultantSelectorValue,
} from "@/components/CoConsultantSelector";
import { OfferPreview } from "./OfferPreview";

const FIELD_DEFAULTS = {
  client_name: "",
  consulting_type: "ki_strategie" as ConsultingType,
  industry: "",
  price_eur: "",
  transcript: "",
  user_notes: "",
};

export function GenerateForm() {
  const [fields, setFields] = useState(FIELD_DEFAULTS);
  const [coConsultant, setCoConsultant] = useState<CoConsultantSelectorValue>(EMPTY_CO_CONSULTANT);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<OfferGenerateResponse | null>(null);
  const previewRef = useRef<HTMLDivElement>(null);

  const update = <K extends keyof typeof fields>(key: K, value: (typeof fields)[K]) =>
    setFields((prev) => ({ ...prev, [key]: value }));

  const resolveCoConsultantId = async (): Promise<string | null> => {
    if (coConsultant.mode === "none") return null;
    if (coConsultant.mode === "existing") return coConsultant.existingId;
    const newC = coConsultant.newConsultant;
    if (!newC.name.trim()) {
      throw new Error("Co-Berater: Name ist Pflicht, wenn ein neuer Berater angelegt wird.");
    }
    const response = await fetch("/api/consultants", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: newC.name.trim(),
        titel: newC.titel?.trim() || null,
        tel: newC.tel?.trim() || null,
        email: newC.email?.trim() || null,
      }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => null);
      throw new Error(data?.error ?? `Berater anlegen fehlgeschlagen (${response.status})`);
    }
    const created = (await response.json()) as Consultant;
    return created.id;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    const price = Number.parseFloat(fields.price_eur);
    if (!Number.isFinite(price) || price <= 0) {
      setError("Bitte einen Preis > 0 angeben.");
      setLoading(false);
      return;
    }
    if (fields.transcript.trim().length < 50) {
      setError("Das Discovery-Transkript muss mindestens 50 Zeichen umfassen.");
      setLoading(false);
      return;
    }

    try {
      const coConsultantId = await resolveCoConsultantId();

      const payload: OfferGenerateRequest = {
        client_name: fields.client_name.trim(),
        consulting_type: fields.consulting_type,
        industry: fields.industry.trim() || null,
        price_eur: price,
        transcript: fields.transcript.trim(),
        user_notes: fields.user_notes.trim() || null,
        co_consultant_id: coConsultantId,
      };

      const response = await fetch("/api/offers/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.error ?? `Request failed: ${response.status}`);
      }
      setResult(data as OfferGenerateResponse);
      requestAnimationFrame(() =>
        previewRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-10">
      <Card>
        <Card.Header>
          <Card.Title>Neues Angebot generieren</Card.Title>
          <Card.Description>
            Discovery-Daten eingeben — die Pipeline zieht passende Bestandsangebote als Few-Shot
            heran und Claude formt daraus einen strukturierten Entwurf.
          </Card.Description>
        </Card.Header>
        <form onSubmit={handleSubmit}>
          <Card.Content className="space-y-6">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Field>
                <Label htmlFor="client_name">Kunde</Label>
                <Input
                  id="client_name"
                  required
                  maxLength={200}
                  value={fields.client_name}
                  onChange={(e) => update("client_name", e.target.value)}
                  disabled={loading}
                  placeholder="Mustermann GmbH"
                />
              </Field>
              <Field>
                <Label htmlFor="industry">Branche (optional)</Label>
                <Input
                  id="industry"
                  maxLength={200}
                  value={fields.industry}
                  onChange={(e) => update("industry", e.target.value)}
                  disabled={loading}
                  placeholder="Maschinenbau"
                />
              </Field>
              <Field>
                <Label htmlFor="consulting_type">Beratungsart</Label>
                <select
                  id="consulting_type"
                  value={fields.consulting_type}
                  onChange={(e) =>
                    update("consulting_type", e.target.value as ConsultingType)
                  }
                  disabled={loading}
                  className="h-10 w-full rounded-md border border-slate/30 bg-ink/40 px-3 text-text outline-none transition focus:border-signal focus:ring-1 focus:ring-signal disabled:opacity-50"
                >
                  {Object.entries(CONSULTING_TYPE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field>
                <Label htmlFor="price_eur">Investition (EUR, exkl. MwSt.)</Label>
                <Input
                  id="price_eur"
                  type="number"
                  inputMode="decimal"
                  min="1"
                  step="any"
                  required
                  value={fields.price_eur}
                  onChange={(e) => update("price_eur", e.target.value)}
                  disabled={loading}
                  placeholder="14500"
                />
              </Field>
            </div>

            <CoConsultantSelector
              value={coConsultant}
              onChange={setCoConsultant}
              disabled={loading}
            />

            <Field>
              <Label htmlFor="transcript">Discovery-Transkript</Label>
              <textarea
                id="transcript"
                required
                minLength={50}
                rows={10}
                value={fields.transcript}
                onChange={(e) => update("transcript", e.target.value)}
                disabled={loading}
                placeholder="Notizen oder Transkript aus dem Discovery-Call …"
                className="w-full rounded-md border border-slate/30 bg-ink/40 p-3 font-mono text-sm text-text outline-none transition focus:border-signal focus:ring-1 focus:ring-signal disabled:opacity-50"
              />
              <p className="text-xs text-text-muted">
                {fields.transcript.length} Zeichen — mindestens 50.
              </p>
            </Field>

            <Field>
              <Label htmlFor="user_notes">Anmerkungen vom Berater (optional)</Label>
              <textarea
                id="user_notes"
                rows={3}
                maxLength={5000}
                value={fields.user_notes}
                onChange={(e) => update("user_notes", e.target.value)}
                disabled={loading}
                placeholder="Pain-Points, Quick-Wins, Hinweise zur Tonalität …"
                className="w-full rounded-md border border-slate/30 bg-ink/40 p-3 text-sm text-text outline-none transition focus:border-signal focus:ring-1 focus:ring-signal disabled:opacity-50"
              />
            </Field>

            {error && (
              <p className="text-sm text-danger" role="alert">
                {error}
              </p>
            )}
          </Card.Content>
          <Card.Footer className="flex items-center justify-between">
            <span className="text-xs text-text-muted">
              Generierung dauert je nach Modell-Latenz ca. 20–60 Sekunden.
            </span>
            <Button type="submit" variant="primary" disabled={loading}>
              {loading ? "Generiere…" : "Angebot generieren"}
            </Button>
          </Card.Footer>
        </form>
      </Card>

      {result && (
        <div ref={previewRef} className="space-y-4">
          <h2 className="font-display text-xl font-semibold tracking-tight text-text-dim">
            Vorschau
          </h2>
          <OfferPreview result={result} />
        </div>
      )}
    </div>
  );
}

function Field({ children }: { children: React.ReactNode }) {
  return <div className="space-y-2">{children}</div>;
}

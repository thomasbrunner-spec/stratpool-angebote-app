"use client";

/**
 * Editable variant of OfferContentView.
 *
 * On save, sends the edited content to PUT /api/offers/[id]/content, which
 * persists it as a new OfferVersion (n+1). The new render-cache is empty so
 * a follow-up render produces a fresh artifact from the edited text.
 */

import { useState } from "react";
import { Button, Card, Input, Label, Textarea } from "@thomasbrunner-spec/design-system";
import type { OfferContent, OfferDetail } from "@/lib/types/offer";

interface OfferContentEditorProps {
  offerId: string;
  initialContent: OfferContent;
  onSaved: (detail: OfferDetail) => void;
  onCancel: () => void;
}

const MAX_BESTANDTEILE = 8;

export function OfferContentEditor({
  offerId,
  initialContent,
  onSaved,
  onCancel,
}: OfferContentEditorProps) {
  const [content, setContent] = useState<OfferContent>(initialContent);
  const [revisionNotes, setRevisionNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = <K extends keyof OfferContent>(key: K, value: OfferContent[K]) => {
    setContent((c) => ({ ...c, [key]: value }));
  };

  const updateBestandteil = (i: number, key: "titel" | "beschreibung", value: string) => {
    setContent((c) => ({
      ...c,
      bestandteile: c.bestandteile.map((b, idx) =>
        idx === i ? { ...b, [key]: value } : b
      ),
    }));
  };

  const addBestandteil = () => {
    if (content.bestandteile.length >= MAX_BESTANDTEILE) return;
    setContent((c) => ({
      ...c,
      bestandteile: [...c.bestandteile, { titel: "", beschreibung: "" }],
    }));
  };

  const removeBestandteil = (i: number) => {
    if (content.bestandteile.length <= 1) return;
    setContent((c) => ({
      ...c,
      bestandteile: c.bestandteile.filter((_, idx) => idx !== i),
    }));
  };

  const handleSave = async () => {
    setError(null);
    if (!validate(content, setError)) return;
    setSaving(true);
    try {
      const response = await fetch(`/api/offers/${offerId}/content`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content,
          revision_notes: revisionNotes.trim() || null,
        }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.error ?? `Speichern fehlgeschlagen: ${response.status}`);
      }
      const detail = (await response.json()) as OfferDetail;
      onSaved(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <Card.Header>
          <Card.Title>Bearbeiten-Modus</Card.Title>
          <Card.Description>
            Beim Speichern wird eine neue Version angelegt. Vorhandene PowerPoint- und
            Word-Renderings hängen an der alten Version und werden beim nächsten Render
            frisch erzeugt.
          </Card.Description>
        </Card.Header>
        <Card.Content className="space-y-4">
          <Field label="Titel" htmlFor="ed-titel">
            <Input
              id="ed-titel"
              value={content.angebot_titel}
              onChange={(e) => update("angebot_titel", e.target.value)}
              maxLength={200}
              disabled={saving}
            />
          </Field>
          <Field label="Kunde" htmlFor="ed-client">
            <Input
              id="ed-client"
              value={content.client_name}
              onChange={(e) => update("client_name", e.target.value)}
              maxLength={200}
              disabled={saving}
            />
          </Field>
        </Card.Content>
      </Card>

      <Field label="Ausgangssituation" htmlFor="ed-aus">
        <Textarea
          id="ed-aus"
          value={content.ausgangssituation}
          onChange={(e) => update("ausgangssituation", e.target.value)}
          rows={6}
          disabled={saving}
        />
      </Field>

      <Field label="Leistungsumfang (Intro)" htmlFor="ed-lui">
        <Textarea
          id="ed-lui"
          value={content.leistungsumfang_intro}
          onChange={(e) => update("leistungsumfang_intro", e.target.value)}
          rows={4}
          disabled={saving}
        />
      </Field>

      <Card>
        <Card.Header>
          <Card.Title>Bestandteile</Card.Title>
          <Card.Description>
            {content.bestandteile.length} / {MAX_BESTANDTEILE} — mind. 1, max. {MAX_BESTANDTEILE}.
          </Card.Description>
        </Card.Header>
        <Card.Content className="space-y-5">
          {content.bestandteile.map((b, i) => (
            <div key={i} className="space-y-2 border-l-2 border-signal/40 pl-4">
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-mono text-xs text-signal">#{i + 1}</span>
                <button
                  type="button"
                  onClick={() => removeBestandteil(i)}
                  disabled={saving || content.bestandteile.length <= 1}
                  className="text-xs text-text-muted hover:text-danger disabled:opacity-30"
                >
                  entfernen
                </button>
              </div>
              <Input
                aria-label={`Titel Bestandteil ${i + 1}`}
                value={b.titel}
                onChange={(e) => updateBestandteil(i, "titel", e.target.value)}
                maxLength={200}
                placeholder="Titel"
                disabled={saving}
              />
              <Textarea
                aria-label={`Beschreibung Bestandteil ${i + 1}`}
                value={b.beschreibung}
                onChange={(e) => updateBestandteil(i, "beschreibung", e.target.value)}
                rows={4}
                placeholder="Beschreibung"
                disabled={saving}
              />
            </div>
          ))}
          <Button
            variant="secondary"
            type="button"
            onClick={addBestandteil}
            disabled={saving || content.bestandteile.length >= MAX_BESTANDTEILE}
          >
            + Bestandteil hinzufügen
          </Button>
        </Card.Content>
      </Card>

      <Field label="Leistungserbringung" htmlFor="ed-erb">
        <Textarea
          id="ed-erb"
          value={content.leistungserbringung}
          onChange={(e) => update("leistungserbringung", e.target.value)}
          rows={4}
          disabled={saving}
        />
      </Field>

      <Field label="Investition" htmlFor="ed-inv">
        <Textarea
          id="ed-inv"
          value={content.investition}
          onChange={(e) => update("investition", e.target.value)}
          rows={4}
          disabled={saving}
        />
      </Field>

      <Field label="Rahmenbedingungen" htmlFor="ed-rahmen">
        <Textarea
          id="ed-rahmen"
          value={content.rahmenbedingungen}
          onChange={(e) => update("rahmenbedingungen", e.target.value)}
          rows={4}
          disabled={saving}
        />
      </Field>

      <Field label="Notiz zur Änderung (optional)" htmlFor="ed-rev">
        <Input
          id="ed-rev"
          value={revisionNotes}
          onChange={(e) => setRevisionNotes(e.target.value)}
          maxLength={2000}
          placeholder="z.B. Investition angepasst, Bestandteil 2 präzisiert"
          disabled={saving}
        />
      </Field>

      {error && (
        <p className="text-sm text-danger" role="alert">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-3">
        <Button variant="primary" onClick={handleSave} disabled={saving}>
          {saving ? "Speichere…" : "Als neue Version speichern"}
        </Button>
        <Button variant="secondary" onClick={onCancel} disabled={saving}>
          Abbrechen
        </Button>
      </div>
    </div>
  );
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
    </div>
  );
}

function validate(c: OfferContent, setError: (msg: string) => void): boolean {
  const required: [string, string][] = [
    ["angebot_titel", c.angebot_titel],
    ["client_name", c.client_name],
    ["ausgangssituation", c.ausgangssituation],
    ["leistungsumfang_intro", c.leistungsumfang_intro],
    ["leistungserbringung", c.leistungserbringung],
    ["investition", c.investition],
    ["rahmenbedingungen", c.rahmenbedingungen],
  ];
  for (const [key, val] of required) {
    if (!val.trim()) {
      setError(`Feld "${key}" darf nicht leer sein.`);
      return false;
    }
  }
  if (c.bestandteile.length === 0 || c.bestandteile.length > MAX_BESTANDTEILE) {
    setError(`Bestandteile: 1 bis ${MAX_BESTANDTEILE} erlaubt.`);
    return false;
  }
  for (let i = 0; i < c.bestandteile.length; i++) {
    const b = c.bestandteile[i];
    if (!b.titel.trim() || !b.beschreibung.trim()) {
      setError(`Bestandteil ${i + 1}: Titel und Beschreibung dürfen nicht leer sein.`);
      return false;
    }
  }
  return true;
}

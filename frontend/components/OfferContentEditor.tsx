"use client";

/**
 * Editable variant of OfferContentView for the v2 storytelling schema.
 *
 * On save, sends the edited content to PUT /api/offers/[id]/content, which
 * persists it as a new OfferVersion (n+1). The render-cache for the new
 * version is empty so a follow-up render produces a fresh artifact from
 * the edited text.
 */

import { useState } from "react";
import { Button, Card, Input, Label, Textarea } from "@thomasbrunner-spec/design-system";
import type {
  OfferContent,
  OfferDetail,
  OfferLeistungsItem,
  OfferMehrwertEbene,
  OfferPhase,
  OfferTechOption,
} from "@/lib/types/offer";

interface OfferContentEditorProps {
  offerId: string;
  initialContent: OfferContent;
  onSaved: (detail: OfferDetail) => void;
  onCancel: () => void;
}

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
            Beim Speichern wird eine neue Version angelegt. Bestehende PowerPoint- und
            Word-Renderings hängen an der alten Version und werden beim nächsten Render
            frisch aus dem hier freigegebenen Text erzeugt.
          </Card.Description>
        </Card.Header>
        <Card.Content className="space-y-4">
          <Field label="Angebotstitel" htmlFor="ed-titel">
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

      <Field label="Management Summary" htmlFor="ed-summary" hint="5–10 Sätze, narrativ">
        <Textarea
          id="ed-summary"
          value={content.management_summary}
          onChange={(e) => update("management_summary", e.target.value)}
          rows={6}
          disabled={saving}
        />
      </Field>

      <Field label="Hook-Quote" htmlFor="ed-hook" hint="Zitierfähiger Insight, 1–2 Sätze">
        <Textarea
          id="ed-hook"
          value={content.hook_quote}
          onChange={(e) => update("hook_quote", e.target.value)}
          rows={3}
          disabled={saving}
        />
      </Field>

      <StringListField
        label="Warum jetzt — Argumente"
        values={content.warum_jetzt_argumente}
        onChange={(v) => update("warum_jetzt_argumente", v)}
        min={2}
        max={5}
        placeholder="z.B. KI-Nutzung im Mittelstand hat sich verdoppelt"
        disabled={saving}
      />

      <Field label="Ausgangssituation" htmlFor="ed-situation">
        <Textarea
          id="ed-situation"
          value={content.ausgangssituation}
          onChange={(e) => update("ausgangssituation", e.target.value)}
          rows={6}
          disabled={saving}
        />
      </Field>

      <StringListField
        label="Erkannte Anwendungsfälle"
        values={content.erkannte_anwendungsfaelle}
        onChange={(v) => update("erkannte_anwendungsfaelle", v)}
        min={3}
        max={10}
        placeholder="z.B. Automatisierter Abgleich von Wareneingangsdifferenzen"
        disabled={saving}
      />

      <Field label="Zielsetzung & Ergebnis" htmlFor="ed-goal">
        <Textarea
          id="ed-goal"
          value={content.zielsetzung_und_ergebnis}
          onChange={(e) => update("zielsetzung_und_ergebnis", e.target.value)}
          rows={5}
          disabled={saving}
        />
      </Field>

      <PhasenEditor
        phasen={content.phasen}
        onChange={(p) => update("phasen", p)}
        disabled={saving}
      />

      <TechOptionsEditor
        options={content.technische_basis}
        onChange={(t) => update("technische_basis", t)}
        disabled={saving}
      />

      <MehrwertEditor
        ebenen={content.mehrwert_3_ebenen}
        onChange={(m) => update("mehrwert_3_ebenen", m)}
        disabled={saving}
      />

      <LeistungsItemsEditor
        items={content.leistungsumfang_items}
        onChange={(it) => update("leistungsumfang_items", it)}
        disabled={saving}
      />

      <Field label="Investition" htmlFor="ed-inv">
        <Textarea
          id="ed-inv"
          value={content.investition}
          onChange={(e) => update("investition", e.target.value)}
          rows={5}
          disabled={saving}
        />
      </Field>

      <Field label="Nächste Schritte" htmlFor="ed-next">
        <Textarea
          id="ed-next"
          value={content.naechste_schritte}
          onChange={(e) => update("naechste_schritte", e.target.value)}
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
          placeholder="z.B. Investition angepasst, Phase 3 präzisiert"
          disabled={saving}
        />
      </Field>

      {error && (
        <p className="text-sm text-danger" role="alert">{error}</p>
      )}

      <div className="flex flex-wrap gap-3">
        <Button variant="primary" onClick={handleSave} disabled={saving}>
          {saving ? "Speichere…" : "Als neue Version speichern"}
        </Button>
        <Button variant="secondary" onClick={onCancel} disabled={saving}>Abbrechen</Button>
      </div>
    </div>
  );
}

// ---------------- nested editors ----------------

function PhasenEditor({
  phasen,
  onChange,
  disabled,
}: {
  phasen: OfferPhase[];
  onChange: (p: OfferPhase[]) => void;
  disabled: boolean;
}) {
  const add = () => {
    if (phasen.length >= 6) return;
    onChange([
      ...phasen,
      {
        nummer: phasen.length + 1,
        titel: "",
        untertitel: "",
        beschreibung: "",
        dauer: "",
        format: "",
        teilnehmer: "",
        moderation: "",
        aktivitaeten: [],
        ergebnis: "",
      },
    ]);
  };
  const remove = (i: number) => {
    if (phasen.length <= 2) return;
    const next = phasen
      .filter((_, idx) => idx !== i)
      .map((p, idx) => ({ ...p, nummer: idx + 1 }));
    onChange(next);
  };
  const updateAt = (i: number, patch: Partial<OfferPhase>) => {
    onChange(phasen.map((p, idx) => (idx === i ? { ...p, ...patch } : p)));
  };

  return (
    <Card>
      <Card.Header>
        <Card.Title>Phasen</Card.Title>
        <Card.Description>{phasen.length} / 6 — mind. 2, max. 6.</Card.Description>
      </Card.Header>
      <Card.Content className="space-y-6">
        {phasen.map((p, i) => (
          <div key={i} className="space-y-2 border-l-2 border-signal/40 pl-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs text-signal">Phase {p.nummer}</span>
              <button
                type="button"
                onClick={() => remove(i)}
                disabled={disabled || phasen.length <= 2}
                className="text-xs text-text-muted hover:text-danger disabled:opacity-30"
              >
                entfernen
              </button>
            </div>
            <Input
              aria-label={`Titel Phase ${p.nummer}`}
              value={p.titel}
              onChange={(e) => updateAt(i, { titel: e.target.value })}
              placeholder="Titel der Phase"
              disabled={disabled}
            />
            <Input
              aria-label={`Untertitel Phase ${p.nummer}`}
              value={p.untertitel ?? ""}
              onChange={(e) => updateAt(i, { untertitel: e.target.value })}
              placeholder="Untertitel (optional, ein Satz)"
              disabled={disabled}
            />
            <Textarea
              aria-label={`Beschreibung Phase ${p.nummer}`}
              value={p.beschreibung}
              onChange={(e) => updateAt(i, { beschreibung: e.target.value })}
              rows={3}
              placeholder="2–4 Sätze, narrativ"
              disabled={disabled}
            />
            <div className="grid gap-2 md:grid-cols-2">
              <Input
                aria-label={`Dauer Phase ${p.nummer}`}
                value={p.dauer ?? ""}
                onChange={(e) => updateAt(i, { dauer: e.target.value })}
                placeholder="Dauer (z.B. ein Tag)"
                disabled={disabled}
              />
              <Input
                aria-label={`Format Phase ${p.nummer}`}
                value={p.format ?? ""}
                onChange={(e) => updateAt(i, { format: e.target.value })}
                placeholder="Format (z.B. vor Ort)"
                disabled={disabled}
              />
              <Input
                aria-label={`Teilnehmer Phase ${p.nummer}`}
                value={p.teilnehmer ?? ""}
                onChange={(e) => updateAt(i, { teilnehmer: e.target.value })}
                placeholder="Teilnehmer"
                disabled={disabled}
              />
              <Input
                aria-label={`Moderation Phase ${p.nummer}`}
                value={p.moderation ?? ""}
                onChange={(e) => updateAt(i, { moderation: e.target.value })}
                placeholder="Moderation"
                disabled={disabled}
              />
            </div>
            <StringListField
              label="Aktivitäten (optional)"
              values={p.aktivitaeten}
              onChange={(v) => updateAt(i, { aktivitaeten: v })}
              min={0}
              max={8}
              placeholder="kurze Aktivität"
              disabled={disabled}
              compact
            />
            <Textarea
              aria-label={`Ergebnis Phase ${p.nummer}`}
              value={p.ergebnis}
              onChange={(e) => updateAt(i, { ergebnis: e.target.value })}
              rows={2}
              placeholder="Ergebnis dieser Phase"
              disabled={disabled}
            />
          </div>
        ))}
        <Button
          variant="secondary"
          type="button"
          onClick={add}
          disabled={disabled || phasen.length >= 6}
        >
          + Phase hinzufügen
        </Button>
      </Card.Content>
    </Card>
  );
}

function TechOptionsEditor({
  options,
  onChange,
  disabled,
}: {
  options: OfferTechOption[];
  onChange: (t: OfferTechOption[]) => void;
  disabled: boolean;
}) {
  const add = () => {
    if (options.length >= 4) return;
    onChange([...options, { titel: "", beschreibung: "" }]);
  };
  const remove = (i: number) => {
    if (options.length <= 2) return;
    onChange(options.filter((_, idx) => idx !== i));
  };
  const updateAt = (i: number, patch: Partial<OfferTechOption>) => {
    onChange(options.map((t, idx) => (idx === i ? { ...t, ...patch } : t)));
  };

  return (
    <Card>
      <Card.Header>
        <Card.Title>Technische Basis</Card.Title>
        <Card.Description>{options.length} / 4 — mind. 2, max. 4.</Card.Description>
      </Card.Header>
      <Card.Content className="space-y-4">
        {options.map((t, i) => (
          <div key={i} className="space-y-2 border-l-2 border-signal/40 pl-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs text-signal">Option {i + 1}</span>
              <button
                type="button"
                onClick={() => remove(i)}
                disabled={disabled || options.length <= 2}
                className="text-xs text-text-muted hover:text-danger disabled:opacity-30"
              >
                entfernen
              </button>
            </div>
            <Input
              aria-label={`Titel Tech-Option ${i + 1}`}
              value={t.titel}
              onChange={(e) => updateAt(i, { titel: e.target.value })}
              placeholder="z.B. Lokal beim Kunden"
              disabled={disabled}
            />
            <Textarea
              aria-label={`Beschreibung Tech-Option ${i + 1}`}
              value={t.beschreibung}
              onChange={(e) => updateAt(i, { beschreibung: e.target.value })}
              rows={3}
              placeholder="Konsequenzen für den Kunden"
              disabled={disabled}
            />
          </div>
        ))}
        <Button variant="secondary" type="button" onClick={add} disabled={disabled || options.length >= 4}>
          + Option hinzufügen
        </Button>
      </Card.Content>
    </Card>
  );
}

function MehrwertEditor({
  ebenen,
  onChange,
  disabled,
}: {
  ebenen: OfferMehrwertEbene[];
  onChange: (m: OfferMehrwertEbene[]) => void;
  disabled: boolean;
}) {
  // Exactly three layers; we don't allow add/remove, just edit content.
  const updateAt = (i: number, patch: Partial<OfferMehrwertEbene>) => {
    onChange(ebenen.map((e, idx) => (idx === i ? { ...e, ...patch } : e)));
  };

  return (
    <Card>
      <Card.Header>
        <Card.Title>Mehrwert auf drei Ebenen</Card.Title>
        <Card.Description>Genau drei Ebenen, je 3–6 Punkte.</Card.Description>
      </Card.Header>
      <Card.Content className="space-y-5">
        {ebenen.map((e, i) => (
          <div key={i} className="space-y-2">
            <Input
              aria-label={`Ebene ${i + 1} Name`}
              value={e.ebene}
              onChange={(ev) => updateAt(i, { ebene: ev.target.value })}
              placeholder="z.B. Strategisch"
              disabled={disabled}
            />
            <StringListField
              label="Punkte"
              values={e.punkte}
              onChange={(v) => updateAt(i, { punkte: v })}
              min={3}
              max={6}
              placeholder="ein konkreter Mehrwert"
              disabled={disabled}
              compact
            />
          </div>
        ))}
      </Card.Content>
    </Card>
  );
}

function LeistungsItemsEditor({
  items,
  onChange,
  disabled,
}: {
  items: OfferLeistungsItem[];
  onChange: (it: OfferLeistungsItem[]) => void;
  disabled: boolean;
}) {
  const add = () => {
    if (items.length >= 12) return;
    onChange([
      ...items,
      { nummer: items.length + 1, titel: "", beschreibung: "" },
    ]);
  };
  const remove = (i: number) => {
    if (items.length <= 4) return;
    onChange(
      items.filter((_, idx) => idx !== i).map((it, idx) => ({ ...it, nummer: idx + 1 }))
    );
  };
  const updateAt = (i: number, patch: Partial<OfferLeistungsItem>) => {
    onChange(items.map((it, idx) => (idx === i ? { ...it, ...patch } : it)));
  };

  return (
    <Card>
      <Card.Header>
        <Card.Title>Was im Angebot enthalten ist</Card.Title>
        <Card.Description>{items.length} / 12 — mind. 4, max. 12.</Card.Description>
      </Card.Header>
      <Card.Content className="space-y-4">
        {items.map((it, i) => (
          <div key={i} className="space-y-2 border-l-2 border-signal/40 pl-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs text-signal">{it.nummer}.</span>
              <button
                type="button"
                onClick={() => remove(i)}
                disabled={disabled || items.length <= 4}
                className="text-xs text-text-muted hover:text-danger disabled:opacity-30"
              >
                entfernen
              </button>
            </div>
            <Input
              aria-label={`Titel Item ${it.nummer}`}
              value={it.titel}
              onChange={(e) => updateAt(i, { titel: e.target.value })}
              placeholder="Titel"
              disabled={disabled}
            />
            <Textarea
              aria-label={`Beschreibung Item ${it.nummer}`}
              value={it.beschreibung}
              onChange={(e) => updateAt(i, { beschreibung: e.target.value })}
              rows={2}
              placeholder="1–3 Sätze, was konkret enthalten ist"
              disabled={disabled}
            />
          </div>
        ))}
        <Button variant="secondary" type="button" onClick={add} disabled={disabled || items.length >= 12}>
          + Item hinzufügen
        </Button>
      </Card.Content>
    </Card>
  );
}

// ---------------- shared bits ----------------

function StringListField({
  label,
  values,
  onChange,
  min,
  max,
  placeholder,
  disabled,
  compact = false,
}: {
  label: string;
  values: string[];
  onChange: (v: string[]) => void;
  min: number;
  max: number;
  placeholder: string;
  disabled: boolean;
  compact?: boolean;
}) {
  const add = () => {
    if (values.length >= max) return;
    onChange([...values, ""]);
  };
  const remove = (i: number) => {
    if (values.length <= min) return;
    onChange(values.filter((_, idx) => idx !== i));
  };
  const updateAt = (i: number, v: string) => {
    onChange(values.map((s, idx) => (idx === i ? v : s)));
  };
  return (
    <div className={compact ? "space-y-1.5" : "space-y-2"}>
      <Label>{label} <span className="font-mono text-xs text-text-muted">({values.length}/{max})</span></Label>
      <div className="space-y-2">
        {values.map((v, i) => (
          <div key={i} className="flex items-start gap-2">
            <Input
              aria-label={`${label} ${i + 1}`}
              value={v}
              onChange={(e) => updateAt(i, e.target.value)}
              placeholder={placeholder}
              disabled={disabled}
            />
            <button
              type="button"
              onClick={() => remove(i)}
              disabled={disabled || values.length <= min}
              className="text-xs text-text-muted hover:text-danger disabled:opacity-30 mt-2"
            >
              ×
            </button>
          </div>
        ))}
        <Button
          variant="secondary"
          type="button"
          onClick={add}
          disabled={disabled || values.length >= max}
        >
          +
        </Button>
      </div>
    </div>
  );
}

function Field({
  label,
  htmlFor,
  hint,
  children,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={htmlFor}>
        {label}
        {hint && <span className="ml-2 font-mono text-xs text-text-muted">{hint}</span>}
      </Label>
      {children}
    </div>
  );
}

function validate(c: OfferContent, setError: (msg: string) => void): boolean {
  const stringFields: [keyof OfferContent, string][] = [
    ["angebot_titel", "Angebotstitel"],
    ["client_name", "Kunde"],
    ["management_summary", "Management Summary"],
    ["hook_quote", "Hook-Quote"],
    ["ausgangssituation", "Ausgangssituation"],
    ["zielsetzung_und_ergebnis", "Zielsetzung & Ergebnis"],
    ["investition", "Investition"],
    ["naechste_schritte", "Nächste Schritte"],
  ];
  for (const [key, label] of stringFields) {
    const v = c[key];
    if (typeof v === "string" && !v.trim()) {
      setError(`Feld "${label}" darf nicht leer sein.`);
      return false;
    }
  }
  if (c.warum_jetzt_argumente.length < 2 || c.warum_jetzt_argumente.some((a) => !a.trim())) {
    setError("Warum jetzt: mind. 2 nicht-leere Argumente.");
    return false;
  }
  if (c.erkannte_anwendungsfaelle.length < 3 || c.erkannte_anwendungsfaelle.some((a) => !a.trim())) {
    setError("Erkannte Anwendungsfälle: mind. 3 nicht-leere Einträge.");
    return false;
  }
  if (c.phasen.length < 2) {
    setError("Phasen: mind. 2.");
    return false;
  }
  for (let i = 0; i < c.phasen.length; i++) {
    const p = c.phasen[i];
    if (!p.titel.trim() || !p.beschreibung.trim() || !p.ergebnis.trim()) {
      setError(`Phase ${i + 1}: Titel, Beschreibung und Ergebnis dürfen nicht leer sein.`);
      return false;
    }
  }
  if (c.technische_basis.length < 2) {
    setError("Technische Basis: mind. 2 Optionen.");
    return false;
  }
  if (c.mehrwert_3_ebenen.length !== 3) {
    setError("Mehrwert: genau 3 Ebenen.");
    return false;
  }
  for (const e of c.mehrwert_3_ebenen) {
    if (!e.ebene.trim() || e.punkte.length < 3 || e.punkte.some((p) => !p.trim())) {
      setError(`Mehrwert-Ebene "${e.ebene || "?"}": Name und mind. 3 nicht-leere Punkte.`);
      return false;
    }
  }
  if (c.leistungsumfang_items.length < 4) {
    setError("Leistungsumfang: mind. 4 Items.");
    return false;
  }
  for (const it of c.leistungsumfang_items) {
    if (!it.titel.trim() || !it.beschreibung.trim()) {
      setError(`Leistungs-Item ${it.nummer}: Titel und Beschreibung dürfen nicht leer sein.`);
      return false;
    }
  }
  return true;
}

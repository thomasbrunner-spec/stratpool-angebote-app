"use client";

import { useEffect, useState } from "react";
import { Input, Label } from "@thomasbrunner-spec/design-system";
import type { Consultant, ConsultantCreate } from "@/lib/types/consultant";

type Mode = "none" | "existing" | "new";

export interface CoConsultantSelectorValue {
  mode: Mode;
  /** ID of an existing consultant — only when mode === "existing". */
  existingId: string | null;
  /** Inline form data — only when mode === "new". */
  newConsultant: ConsultantCreate;
}

interface CoConsultantSelectorProps {
  value: CoConsultantSelectorValue;
  onChange: (value: CoConsultantSelectorValue) => void;
  disabled?: boolean;
}

const EMPTY_NEW: ConsultantCreate = {
  name: "",
  titel: null,
  tel: null,
  email: null,
};

export function CoConsultantSelector({
  value,
  onChange,
  disabled,
}: CoConsultantSelectorProps) {
  const [consultants, setConsultants] = useState<Consultant[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/consultants")
      .then(async (r) => {
        if (!r.ok) {
          const data = await r.json().catch(() => null);
          throw new Error(data?.error ?? `Liste konnte nicht geladen werden (${r.status})`);
        }
        return r.json() as Promise<Consultant[]>;
      })
      .then((list) => {
        if (!cancelled) setConsultants(list);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(err instanceof Error ? err.message : "Unknown error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSelectChange = (raw: string) => {
    if (raw === "__none__") {
      onChange({ mode: "none", existingId: null, newConsultant: EMPTY_NEW });
    } else if (raw === "__new__") {
      onChange({ mode: "new", existingId: null, newConsultant: EMPTY_NEW });
    } else {
      onChange({ mode: "existing", existingId: raw, newConsultant: EMPTY_NEW });
    }
  };

  const updateNew = <K extends keyof ConsultantCreate>(
    key: K,
    raw: string
  ) => {
    onChange({
      ...value,
      newConsultant: { ...value.newConsultant, [key]: raw || null },
    });
  };

  const selectValue =
    value.mode === "none"
      ? "__none__"
      : value.mode === "new"
        ? "__new__"
        : value.existingId ?? "__none__";

  return (
    <div className="space-y-3">
      <Label htmlFor="co_consultant">Co-Berater (optional)</Label>
      <select
        id="co_consultant"
        value={selectValue}
        onChange={(e) => handleSelectChange(e.target.value)}
        disabled={disabled || consultants === null}
        className="h-10 w-full rounded-md border border-slate/30 bg-ink/40 px-3 text-text outline-none transition focus:border-signal focus:ring-1 focus:ring-signal disabled:opacity-50"
      >
        <option value="__none__">— kein Co-Berater —</option>
        {consultants?.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
            {c.titel ? ` · ${c.titel}` : ""}
          </option>
        ))}
        <option value="__new__">+ Neuen Berater anlegen…</option>
      </select>

      {loadError && (
        <p className="text-xs text-danger">Konnte Berater-Liste nicht laden: {loadError}</p>
      )}

      {value.mode === "new" && (
        <div className="grid grid-cols-1 gap-3 rounded-md border border-slate/30 bg-ink/20 p-4 sm:grid-cols-2">
          <div className="space-y-1">
            <Label htmlFor="co_new_name" className="text-xs">Name</Label>
            <Input
              id="co_new_name"
              required
              value={value.newConsultant.name}
              onChange={(e) => updateNew("name", e.target.value)}
              disabled={disabled}
              placeholder="Max Mustermann"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="co_new_titel" className="text-xs">Titel / Rolle</Label>
            <Input
              id="co_new_titel"
              value={value.newConsultant.titel ?? ""}
              onChange={(e) => updateNew("titel", e.target.value)}
              disabled={disabled}
              placeholder="Senior Partner"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="co_new_tel" className="text-xs">Telefon</Label>
            <Input
              id="co_new_tel"
              value={value.newConsultant.tel ?? ""}
              onChange={(e) => updateNew("tel", e.target.value)}
              disabled={disabled}
              placeholder="+49 …"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="co_new_email" className="text-xs">E-Mail</Label>
            <Input
              id="co_new_email"
              type="email"
              value={value.newConsultant.email ?? ""}
              onChange={(e) => updateNew("email", e.target.value)}
              disabled={disabled}
              placeholder="name@era-group.com"
            />
          </div>
        </div>
      )}
    </div>
  );
}

export const EMPTY_CO_CONSULTANT: CoConsultantSelectorValue = {
  mode: "none",
  existingId: null,
  newConsultant: EMPTY_NEW,
};

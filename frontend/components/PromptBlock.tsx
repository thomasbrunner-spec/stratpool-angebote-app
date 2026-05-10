"use client";

import { useState } from "react";

interface PromptBlockProps {
  label: string;
  text: string;
}

/**
 * Read-only display of a prompt with a copy-to-clipboard affordance.
 * Used on /prompts.
 */
export function PromptBlock({ label, text }: PromptBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard API can fail in non-secure contexts; silently degrade.
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-xs uppercase tracking-wider text-text-muted">{label}</h3>
        <button
          type="button"
          onClick={handleCopy}
          className="font-mono text-xs text-text-muted transition hover:text-signal"
        >
          {copied ? "kopiert ✓" : "kopieren"}
        </button>
      </div>
      <pre className="overflow-x-auto rounded-md border border-slate/30 bg-ink/40 p-4 font-mono text-xs leading-relaxed text-text-dim">
        {text}
      </pre>
    </div>
  );
}

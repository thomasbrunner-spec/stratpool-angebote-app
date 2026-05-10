"use client";

import { useState } from "react";
import { Badge, Card } from "@thomasbrunner-spec/design-system";
import { DownloadButtons } from "@/components/DownloadButtons";
import { OfferContentSection } from "@/components/OfferContentSection";
import type { OfferContent, OfferDetail, OfferGenerateResponse } from "@/lib/types/offer";

interface OfferPreviewProps {
  result: OfferGenerateResponse;
}

export function OfferPreview({ result }: OfferPreviewProps) {
  // Track edits locally so the preview reflects the latest saved version
  // without forcing a navigation away from /angebote/neu.
  const [content, setContent] = useState<OfferContent>(result.content);
  const [versionNumber, setVersionNumber] = useState<number>(result.version_number);

  const handleSaved = (detail: OfferDetail) => {
    setContent(detail.content);
    setVersionNumber(detail.version_number);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h2 className="font-display text-2xl font-semibold tracking-tight">
            {content.angebot_titel}
          </h2>
          <p className="text-text-dim">
            Für <span className="text-text">{content.client_name}</span>
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <Badge variant="success">DRAFT v{versionNumber}</Badge>
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
            Tipp: zuerst den Text bearbeiten und speichern, dann rendern — so renderst
            du genau die freigegebene Fassung.
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <DownloadButtons offerId={result.offer_id} />
        </Card.Content>
      </Card>

      <OfferContentSection
        offerId={result.offer_id}
        content={content}
        onSaved={handleSaved}
      />

      <Meta result={result} versionNumber={versionNumber} />
    </div>
  );
}

function Meta({
  result,
  versionNumber,
}: {
  result: OfferGenerateResponse;
  versionNumber: number;
}) {
  return (
    <Card>
      <Card.Header>
        <Card.Title>Metadaten</Card.Title>
        <Card.Description>
          Aktuelle Version: v{versionNumber}. Jede Bearbeitung legt eine neue Version an.
        </Card.Description>
      </Card.Header>
      <Card.Content className="grid grid-cols-1 gap-3 font-mono text-xs sm:grid-cols-2">
        <MetaRow label="offer_id" value={result.offer_id} />
        <MetaRow label="generated_at" value={result.created_at} />
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

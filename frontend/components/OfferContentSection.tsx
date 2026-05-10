"use client";

/**
 * View/Edit-toggling wrapper around the offer content.
 *
 * Used on both the preview page (after generate) and the detail page so the
 * user can edit the structured content before rendering Word/PowerPoint.
 * Saving creates a new OfferVersion (handled by the backend); on success we
 * either bubble the new version up via onSaved (preview) or call
 * router.refresh() (detail) so the page re-fetches.
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@thomasbrunner-spec/design-system";
import { OfferContentEditor } from "./OfferContentEditor";
import { OfferContentView } from "./OfferContentView";
import type { OfferContent, OfferDetail } from "@/lib/types/offer";

interface OfferContentSectionProps {
  offerId: string;
  content: OfferContent;
  /** Optional: preview page passes a setter so it can replace its local state. */
  onSaved?: (detail: OfferDetail) => void;
}

export function OfferContentSection({
  offerId,
  content,
  onSaved,
}: OfferContentSectionProps) {
  const [editing, setEditing] = useState(false);
  const router = useRouter();

  if (editing) {
    return (
      <OfferContentEditor
        offerId={offerId}
        initialContent={content}
        onCancel={() => setEditing(false)}
        onSaved={(detail) => {
          setEditing(false);
          if (onSaved) {
            onSaved(detail);
          } else {
            router.refresh();
          }
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button variant="secondary" onClick={() => setEditing(true)}>
          Bearbeiten
        </Button>
      </div>
      <OfferContentView content={content} />
    </div>
  );
}

import { Badge } from "@thomasbrunner-spec/design-system";
import { OFFER_STATUS_LABELS, type OfferStatus } from "@/lib/types/offer";

const STATUS_VARIANT: Record<
  OfferStatus,
  "muted" | "warning" | "success" | "danger"
> = {
  draft: "muted",
  sent: "warning",
  won: "success",
  lost: "danger",
};

export function StatusBadge({ status }: { status: OfferStatus }) {
  return <Badge variant={STATUS_VARIANT[status]}>{OFFER_STATUS_LABELS[status]}</Badge>;
}

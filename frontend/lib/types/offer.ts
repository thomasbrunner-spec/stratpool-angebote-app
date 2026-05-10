/**
 * TypeScript mirror of backend/app/schemas/offer.py — keep in sync.
 */

export type ConsultingType =
  | "ki_strategie"
  | "ai_design_sprint"
  | "prozessberatung"
  | "workshop";

export type OfferStatus = "draft" | "sent" | "won" | "lost";

export const CONSULTING_TYPE_LABELS: Record<ConsultingType, string> = {
  ki_strategie: "KI-Strategie",
  ai_design_sprint: "AI Design Sprint",
  prozessberatung: "Prozessberatung",
  workshop: "Workshop",
};

export interface OfferGenerateRequest {
  client_name: string;
  consulting_type: ConsultingType;
  industry: string | null;
  price_eur: number;
  transcript: string;
  user_notes: string | null;
  co_consultant_id: string | null;
}

export interface OfferContentBestandteil {
  titel: string;
  beschreibung: string;
}

export interface OfferContent {
  angebot_titel: string;
  client_name: string;
  ausgangssituation: string;
  leistungsumfang_intro: string;
  bestandteile: OfferContentBestandteil[];
  leistungserbringung: string;
  investition: string;
  rahmenbedingungen: string;
}

export interface OfferGenerateResponse {
  offer_id: string;
  version_id: string;
  version_number: number;
  content: OfferContent;
  retrieved_offer_ids: string[];
  created_at: string;
}

export const OFFER_STATUS_LABELS: Record<OfferStatus, string> = {
  draft: "Entwurf",
  sent: "Offen",
  won: "Gewonnen",
  lost: "Verloren",
};

export interface OfferListItem {
  id: string;
  client_name: string;
  industry: string | null;
  consulting_type: ConsultingType;
  status: OfferStatus;
  price_eur: number | string | null;
  created_at: string;
  latest_version_number: number;
}

export interface OfferDetail {
  id: string;
  client_name: string;
  industry: string | null;
  consulting_type: ConsultingType;
  status: OfferStatus;
  price_eur: number | string | null;
  created_at: string;
  updated_at: string;
  version_id: string;
  version_number: number;
  version_created_at: string;
  content: OfferContent;
  co_consultant_id: string | null;
  co_consultant_name: string | null;
}

export interface OfferStatusUpdate {
  status: OfferStatus;
}

export interface OfferContentUpdate {
  content: OfferContent;
  revision_notes: string | null;
}

export interface OfferRenderResponse {
  offer_id: string;
  version_id: string;
  version_number: number;
  pptx_url: string | null;
  word_url: string | null;
  filename_prefix: string;
}

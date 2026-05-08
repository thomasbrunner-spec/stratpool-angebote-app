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

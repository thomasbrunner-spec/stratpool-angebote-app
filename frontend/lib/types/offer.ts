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

// Schema v2 — keep in sync with backend/app/schemas/offer.py.

export interface OfferPhase {
  nummer: number;
  titel: string;
  untertitel?: string | null;
  beschreibung: string;
  dauer?: string | null;
  format?: string | null;
  teilnehmer?: string | null;
  moderation?: string | null;
  aktivitaeten: string[];
  ergebnis: string;
}

export interface OfferTechOption {
  titel: string;
  beschreibung: string;
}

export interface OfferMehrwertEbene {
  ebene: string;
  punkte: string[];
}

export interface OfferLeistungsItem {
  nummer: number;
  titel: string;
  beschreibung: string;
}

export interface OfferContent {
  angebot_titel: string;
  client_name: string;
  management_summary: string;
  hook_quote: string;
  warum_jetzt_argumente: string[];
  ausgangssituation: string;
  erkannte_anwendungsfaelle: string[];
  zielsetzung_und_ergebnis: string;
  phasen: OfferPhase[];
  technische_basis: OfferTechOption[];
  mehrwert_3_ebenen: OfferMehrwertEbene[];
  leistungsumfang_items: OfferLeistungsItem[];
  investition: string;
  naechste_schritte: string;
}

export interface OfferGenerateResponse {
  offer_id: string;
  version_id: string;
  version_number: number;
  content: OfferContent;
  retrieved_offer_ids: string[];
  knowledge_chunk_count: number;
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

export interface OfferVersionSummary {
  id: string;
  version_number: number;
  revision_notes: string | null;
  created_at: string;
  is_current: boolean;
}

export interface OfferVersionDetail {
  offer_id: string;
  version_id: string;
  version_number: number;
  revision_notes: string | null;
  created_at: string;
  is_current: boolean;
  content: OfferContent;
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

export type JobStatus =
  | "queued"
  | "running"
  | "complete"
  | "failed"
  | "not_found";

export interface OfferJobCreateResponse {
  job_id: string;
  status: JobStatus;
}

export interface OfferJobStatusResponse {
  job_id: string;
  status: JobStatus;
  enqueue_time: string | null;
  start_time: string | null;
  finish_time: string | null;
  result: OfferGenerateResponse | null;
  error: string | null;
}

export interface OfferRenderJobStatusResponse {
  job_id: string;
  status: JobStatus;
  enqueue_time: string | null;
  start_time: string | null;
  finish_time: string | null;
  result: OfferRenderResponse | null;
  error: string | null;
}

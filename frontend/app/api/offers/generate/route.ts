/**
 * Proxy route: forwards offer-generation requests to the FastAPI backend
 * with the Supabase auth token attached.
 *
 * /api/offers/generate → FastAPI /api/v1/offers/generate
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { OfferGenerateResponse } from "@/lib/types/offer";

// Voyage + Claude can take 20-60s for an offer.
export const maxDuration = 120;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const data = await apiCall<OfferGenerateResponse>("/api/v1/offers/generate", {
      method: "POST",
      body: JSON.stringify(body),
    });
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

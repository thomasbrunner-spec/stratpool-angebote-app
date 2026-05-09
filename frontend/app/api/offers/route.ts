/**
 * Proxy: GET /api/offers → FastAPI /api/v1/offers
 */

import { NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { OfferListItem } from "@/lib/types/offer";

export async function GET() {
  try {
    const data = await apiCall<OfferListItem[]>("/api/v1/offers");
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

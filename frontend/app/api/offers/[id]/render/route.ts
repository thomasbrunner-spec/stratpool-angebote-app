/**
 * Proxy: POST /api/offers/[id]/render → FastAPI /api/v1/offers/{id}/render
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { OfferRenderResponse } from "@/lib/types/offer";

// Render can take a few seconds for the first PPT generation.
export const maxDuration = 60;

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function POST(_request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  try {
    const data = await apiCall<OfferRenderResponse>(
      `/api/v1/offers/${id}/render`,
      { method: "POST" }
    );
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

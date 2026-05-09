/**
 * Proxy: POST /api/offers/[id]/render → FastAPI /api/v1/offers/{id}/render
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { OfferRenderResponse } from "@/lib/types/offer";

// Anthropic skill + code-execution rendering routinely takes 2–5 minutes.
// The Vercel/Coolify edge limit is 10 minutes; we leave headroom.
export const maxDuration = 600;

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  const format = request.nextUrl.searchParams.get("format") ?? "pptx";
  try {
    const data = await apiCall<OfferRenderResponse>(
      `/api/v1/offers/${id}/render?format=${encodeURIComponent(format)}`,
      { method: "POST" }
    );
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

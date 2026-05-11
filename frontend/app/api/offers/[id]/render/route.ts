/**
 * Proxy: POST /api/offers/[id]/render → FastAPI /api/v1/offers/{id}/render
 *
 * Enqueues an async render job. The backend returns 202 + job_id;
 * the client then polls /api/offers/render/jobs/[jobId].
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { OfferJobCreateResponse } from "@/lib/types/offer";

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  const format = request.nextUrl.searchParams.get("format") ?? "pptx";
  try {
    const data = await apiCall<OfferJobCreateResponse>(
      `/api/v1/offers/${id}/render?format=${encodeURIComponent(format)}`,
      { method: "POST" },
    );
    return NextResponse.json(data, { status: 202 });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

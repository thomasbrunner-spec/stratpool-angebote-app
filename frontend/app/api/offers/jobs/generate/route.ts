/**
 * Proxy: POST /api/offers/jobs/generate → FastAPI /api/v1/offers/jobs/generate
 *
 * Enqueues an async offer-generation job. The backend returns immediately
 * with a job_id; the client then polls /api/offers/jobs/[jobId].
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { OfferJobCreateResponse } from "@/lib/types/offer";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const data = await apiCall<OfferJobCreateResponse>(
      "/api/v1/offers/jobs/generate",
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    );
    return NextResponse.json(data, { status: 202 });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

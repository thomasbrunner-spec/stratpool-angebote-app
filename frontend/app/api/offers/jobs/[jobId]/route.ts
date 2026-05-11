/**
 * Proxy: GET /api/offers/jobs/[jobId] → FastAPI /api/v1/offers/jobs/{job_id}
 *
 * Status poll for an enqueued offer-generation job. Returns the materialised
 * offer in `result` once status === 'complete'.
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { OfferJobStatusResponse } from "@/lib/types/offer";

interface RouteContext {
  params: Promise<{ jobId: string }>;
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const { jobId } = await context.params;
  try {
    const data = await apiCall<OfferJobStatusResponse>(
      `/api/v1/offers/jobs/${jobId}`,
    );
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

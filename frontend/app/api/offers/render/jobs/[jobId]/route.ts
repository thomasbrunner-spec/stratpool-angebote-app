/**
 * Proxy: GET /api/offers/render/jobs/[jobId]
 *   → FastAPI /api/v1/offers/render/jobs/{job_id}
 *
 * Status poll for an enqueued render job. Returns `result` with signed
 * pptx/word URLs once status === 'complete'.
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { OfferRenderJobStatusResponse } from "@/lib/types/offer";

interface RouteContext {
  params: Promise<{ jobId: string }>;
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const { jobId } = await context.params;
  try {
    const data = await apiCall<OfferRenderJobStatusResponse>(
      `/api/v1/offers/render/jobs/${jobId}`,
    );
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

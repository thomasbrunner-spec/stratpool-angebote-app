/**
 * Proxy: PUT /api/offers/[id]/content → FastAPI /api/v1/offers/{id}/content
 *
 * Saves edited offer content as a new version (latest.version_number + 1).
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { OfferDetail } from "@/lib/types/offer";

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function PUT(request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  try {
    const body = await request.json();
    const data = await apiCall<OfferDetail>(`/api/v1/offers/${id}/content`, {
      method: "PUT",
      body: JSON.stringify(body),
    });
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

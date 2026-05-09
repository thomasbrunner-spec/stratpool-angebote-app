/**
 * Proxy: GET/PATCH /api/offers/[id] → FastAPI /api/v1/offers/{id}
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { OfferDetail } from "@/lib/types/offer";

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  try {
    const data = await apiCall<OfferDetail>(`/api/v1/offers/${id}`);
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  try {
    const body = await request.json();
    const data = await apiCall<OfferDetail>(`/api/v1/offers/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * Proxy: GET /api/hedy/sessions/[sessionId] → FastAPI /api/v1/hedy/sessions/{id}
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { HedySessionDetail } from "@/lib/types/hedy";

interface RouteContext {
  params: Promise<{ sessionId: string }>;
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const { sessionId } = await context.params;
  try {
    const data = await apiCall<HedySessionDetail>(
      `/api/v1/hedy/sessions/${encodeURIComponent(sessionId)}`,
    );
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}

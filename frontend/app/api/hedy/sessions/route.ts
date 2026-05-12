/**
 * Proxy: GET /api/hedy/sessions → FastAPI /api/v1/hedy/sessions
 *
 * Forwards `limit`, `after`, and `q` query params straight through. The Hedy
 * API key lives on the backend; the browser never sees it.
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { HedySessionList } from "@/lib/types/hedy";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const params = new URLSearchParams();
  const limit = searchParams.get("limit");
  const after = searchParams.get("after");
  const q = searchParams.get("q");
  if (limit) params.set("limit", limit);
  if (after) params.set("after", after);
  if (q) params.set("q", q);
  const qs = params.toString();
  try {
    const data = await apiCall<HedySessionList>(
      `/api/v1/hedy/sessions${qs ? `?${qs}` : ""}`,
    );
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}

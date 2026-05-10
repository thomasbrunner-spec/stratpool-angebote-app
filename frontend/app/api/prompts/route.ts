/**
 * Proxy: GET /api/prompts → FastAPI /api/v1/prompts
 */

import { NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { PromptsResponse } from "@/lib/types/prompts";

export async function GET() {
  try {
    const data = await apiCall<PromptsResponse>("/api/v1/prompts");
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

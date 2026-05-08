/**
 * Proxy route: forwards requests to the FastAPI backend with auth token.
 *
 * /api/hello/haiku → FastAPI /api/v1/hello/haiku
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const data = await apiCall("/api/v1/hello/haiku", {
      method: "POST",
      body: JSON.stringify(body),
    });
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

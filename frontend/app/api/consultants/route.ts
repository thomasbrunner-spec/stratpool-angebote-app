/**
 * Proxy: GET /api/consultants and POST /api/consultants → FastAPI /api/v1/consultants
 */

import { NextRequest, NextResponse } from "next/server";
import { apiCall } from "@/lib/api";
import type { Consultant } from "@/lib/types/consultant";

export async function GET() {
  try {
    const data = await apiCall<Consultant[]>("/api/v1/consultants");
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const data = await apiCall<Consultant>("/api/v1/consultants", {
      method: "POST",
      body: JSON.stringify(body),
    });
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

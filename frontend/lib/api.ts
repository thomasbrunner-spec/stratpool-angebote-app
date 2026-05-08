/**
 * Helper for calling the FastAPI backend with the Supabase access token.
 */

import { createClient } from "@/lib/supabase/server";

export interface ApiCallOptions extends RequestInit {
  /** Override the API base URL (defaults to env var) */
  baseUrl?: string;
}

/**
 * Fetch from the FastAPI backend, automatically attaching the user's auth token.
 * Use in Server Components, Server Actions, or Route Handlers.
 */
export async function apiCall<T = unknown>(
  path: string,
  options: ApiCallOptions = {}
): Promise<T> {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const baseUrl = options.baseUrl || process.env.BACKEND_API_URL || "http://backend:8000";
  const url = `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (session?.access_token) {
    (headers as Record<string, string>).Authorization = `Bearer ${session.access_token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
    cache: options.cache ?? "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${response.status}: ${text || response.statusText}`);
  }

  return response.json() as Promise<T>;
}

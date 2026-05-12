/**
 * Types mirroring the FastAPI Hedy passthrough routes.
 *
 * Field aliases match what Pydantic serialises (camelCase via
 * `serialization_alias` in `app/schemas/hedy.py`).
 */

export interface HedySessionListItem {
  sessionId: string;
  title: string;
  startTime: string;
  durationMinutes: number | null;
}

export interface HedySessionList {
  items: HedySessionListItem[];
  hasMore: boolean;
  nextCursor: string | null;
}

export interface HedySessionDetail {
  sessionId: string;
  title: string;
  startTime: string;
  transcript: string;
  sessionNotes: string | null;
}

"""Hedy meeting-assistant REST client.

Wraps the subset of https://api.hedy.bot/v1/ we need for the offer flow:
list sessions (paginated, optional title substring filter) and fetch a single
session's transcript + notes. Bearer-auth, async httpx.

Notes on the title filter
-------------------------
Hedy's `/sessions` endpoint has no server-side search parameter. To keep the
picker usable when a user has hundreds of sessions, we paginate through pages
client-side until we either fill the requested `limit` of matches or run out
of pages. Capped at MAX_PAGES_FOR_SEARCH to keep latency bounded.
"""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from app.config import get_settings
from app.schemas.hedy import HedySessionDetail, HedySessionList, HedySessionListItem

settings = get_settings()

# Hedy returns up to 100 rows per page; we never need more in a single call.
_PAGE_SIZE = 100
# Bounded scan when a search term is set — 5 pages × 100 = 500 sessions max.
_MAX_PAGES_FOR_SEARCH = 5

_client: httpx.AsyncClient | None = None


class HedyConfigError(RuntimeError):
    """Raised when the Hedy API key is not configured."""


class HedyApiError(RuntimeError):
    """Raised when the Hedy API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


def _require_client() -> httpx.AsyncClient:
    """Lazy-init the shared httpx client. Raises if the key is missing."""
    if not settings.hedy_api_key:
        raise HedyConfigError(
            "HEDY_API_KEY is not set — configure it in .env (and in Coolify "
            "for production) before using the Hedy integration."
        )
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.hedy_base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {settings.hedy_api_key}",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
    return _client


async def close_client() -> None:
    """Close the shared client — call on app shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    client = _require_client()
    try:
        response = await client.get(path, params=params)
    except httpx.HTTPError as exc:
        raise HedyApiError(502, f"Hedy API unreachable: {exc}") from exc
    if response.status_code >= 400:
        # Hedy returns JSON errors with an `error`/`message` field; fall back
        # to raw text if the body isn't JSON.
        try:
            body = response.json()
            msg = body.get("message") or body.get("error") or response.text
        except Exception:
            msg = response.text
        raise HedyApiError(response.status_code, str(msg)[:400])
    return response.json()


def _coerce_item(raw: dict[str, Any]) -> HedySessionListItem:
    """Convert one raw Hedy row into our schema, tolerating missing fields."""
    return HedySessionListItem.model_validate(
        {
            "session_id": raw.get("sessionId") or raw.get("id"),
            "title": raw.get("title") or "(ohne Titel)",
            "start_time": raw.get("startTime"),
            "duration_minutes": raw.get("duration"),
        }
    )


async def list_sessions(
    *,
    limit: int = 20,
    after: str | None = None,
    search: str | None = None,
) -> HedySessionList:
    """List Hedy sessions, newest first.

    When `search` is set we paginate client-side until we collect `limit`
    title-substring matches or hit `_MAX_PAGES_FOR_SEARCH`. Without a search
    term we pass `limit` straight through and surface Hedy's own pagination
    cursor.
    """
    limit = max(1, min(limit, 100))
    needle = search.strip().lower() if search else None

    if not needle:
        payload = await _get(
            "/sessions",
            params={"limit": limit, **({"after": after} if after else {})},
        )
        data = payload.get("data") or []
        pagination = payload.get("pagination") or {}
        return HedySessionList(
            items=[_coerce_item(row) for row in data],
            has_more=bool(pagination.get("hasMore")),
            next_cursor=pagination.get("next"),
        )

    # Title-filter path: scan up to N pages.
    matches: list[HedySessionListItem] = []
    cursor = after
    has_more = False
    next_cursor: str | None = None
    for _ in range(_MAX_PAGES_FOR_SEARCH):
        payload = await _get(
            "/sessions",
            params={"limit": _PAGE_SIZE, **({"after": cursor} if cursor else {})},
        )
        rows = payload.get("data") or []
        pagination = payload.get("pagination") or {}
        for row in rows:
            title = (row.get("title") or "").lower()
            if needle in title:
                matches.append(_coerce_item(row))
                if len(matches) >= limit:
                    has_more = bool(pagination.get("hasMore")) or len(rows) > rows.index(row) + 1
                    next_cursor = pagination.get("next")
                    return HedySessionList(
                        items=matches,
                        has_more=has_more,
                        next_cursor=next_cursor,
                    )
        if not pagination.get("hasMore"):
            break
        cursor = pagination.get("next")
        if not cursor:
            break

    return HedySessionList(items=matches, has_more=False, next_cursor=None)


async def get_session(session_id: str) -> HedySessionDetail:
    """Fetch one session's transcript + notes."""
    raw = await _get(f"/sessions/{session_id}")
    # Hedy wraps detail responses in {success, data: {...}} too in some
    # versions; tolerate both shapes.
    body = raw.get("data") if isinstance(raw.get("data"), dict) else raw
    transcript = (
        body.get("cleaned_transcript")
        or body.get("transcript")
        or ""
    )
    return HedySessionDetail.model_validate(
        {
            "session_id": body.get("sessionId") or session_id,
            "title": body.get("title") or "(ohne Titel)",
            "start_time": body.get("startTime"),
            "transcript": transcript,
            "session_notes": body.get("session_notes") or None,
        }
    )


async def health_check() -> dict[str, Any]:
    """Probe the Hedy API with a minimal list call."""
    if not settings.hedy_api_key:
        return {"ok": False, "configured": False}
    try:
        await _get("/sessions", params={"limit": 1})
        return {"ok": True, "configured": True}
    except HedyApiError as exc:
        logger.warning(f"Hedy health check failed: {exc.status_code} {exc}")
        return {"ok": False, "configured": True, "error": str(exc), "status_code": exc.status_code}

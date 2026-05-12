"""Hedy passthrough routes — list sessions and fetch one session's transcript.

The frontend uses these to pre-fill the discovery-transcript field on the
new-offer form. The Hedy API key never leaves the backend.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from loguru import logger

from app.schemas.hedy import HedySessionDetail, HedySessionList
from app.services import hedy as hedy_service
from app.services.auth import CurrentUser

router = APIRouter(prefix="/hedy", tags=["hedy"])


def _to_http(exc: hedy_service.HedyApiError) -> HTTPException:
    """Translate a HedyApiError into an HTTPException with a sensible status."""
    upstream = exc.status_code
    if upstream == 401:
        # The user's request was authenticated against our app; this 401 means
        # *our* Hedy key is wrong. Surface as 502 so the frontend doesn't log
        # the user out.
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hedy API rejected our credentials — check HEDY_API_KEY.",
        )
    if upstream == 404:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if upstream == 429:
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Hedy rate limit hit — retry shortly.",
        )
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.get("/sessions", response_model=HedySessionList)
async def list_hedy_sessions(
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    after: Annotated[str | None, Query(description="Hedy pagination cursor")] = None,
    q: Annotated[
        str | None,
        Query(description="Optional title substring filter (case-insensitive)"),
    ] = None,
) -> HedySessionList:
    """List Hedy sessions, newest first. Optional title filter via `q`."""
    try:
        return await hedy_service.list_sessions(limit=limit, after=after, search=q)
    except hedy_service.HedyConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except hedy_service.HedyApiError as exc:
        logger.warning(f"[hedy] list_sessions upstream error: {exc.status_code} {exc}")
        raise _to_http(exc) from exc


@router.get("/sessions/{session_id}", response_model=HedySessionDetail)
async def get_hedy_session(
    session_id: str,
    user: CurrentUser,
) -> HedySessionDetail:
    """Fetch one Hedy session — returns cleaned transcript + session notes."""
    try:
        return await hedy_service.get_session(session_id)
    except hedy_service.HedyConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except hedy_service.HedyApiError as exc:
        logger.warning(
            f"[hedy] get_session({session_id}) upstream error: "
            f"{exc.status_code} {exc}"
        )
        raise _to_http(exc) from exc

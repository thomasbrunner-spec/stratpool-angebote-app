"""Tests for the Hedy integration: route auth gate + client behaviour."""

from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services import hedy as hedy_service


# ---------------- Route auth smoke ----------------


@pytest.mark.asyncio
async def test_list_hedy_sessions_requires_auth() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/hedy/sessions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_hedy_session_requires_auth() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/hedy/sessions/abc123")
    assert response.status_code == 401


# ---------------- HedyClient unit ----------------


@pytest.fixture
def hedy_mocked(monkeypatch: pytest.MonkeyPatch):
    """Install a MockTransport in place of the shared httpx client.

    Yields a list captured request URLs so tests can assert what we called.
    """
    monkeypatch.setattr(hedy_service.settings, "hedy_api_key", "test-key")

    captured: list[httpx.Request] = []
    responses: dict[str, httpx.Response] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        # Match by path so query strings don't matter to the key.
        for path, resp in responses.items():
            if request.url.path.endswith(path):
                return resp
        return httpx.Response(404, json={"message": "not in mock"})

    transport = httpx.MockTransport(handler)
    mock_client = httpx.AsyncClient(
        transport=transport,
        base_url="https://api.hedy.bot/v1",
        headers={"Authorization": "Bearer test-key"},
    )
    monkeypatch.setattr(hedy_service, "_client", mock_client)

    return captured, responses


@pytest.mark.asyncio
async def test_list_sessions_passes_limit_and_parses_pagination(hedy_mocked) -> None:
    captured, responses = hedy_mocked
    responses["/sessions"] = httpx.Response(
        200,
        json={
            "success": True,
            "data": [
                {
                    "sessionId": "s1",
                    "title": "Acme - Discovery",
                    "startTime": "2026-05-10T09:00:00Z",
                    "duration": 42,
                },
                {
                    "sessionId": "s2",
                    "title": "Beta - Kickoff",
                    "startTime": "2026-05-09T14:00:00Z",
                    "duration": 30,
                },
            ],
            "pagination": {"hasMore": True, "next": "cursor-2"},
        },
    )

    result = await hedy_service.list_sessions(limit=5)

    assert [i.session_id for i in result.items] == ["s1", "s2"]
    assert result.has_more is True
    assert result.next_cursor == "cursor-2"
    assert captured[0].url.params["limit"] == "5"


@pytest.mark.asyncio
async def test_list_sessions_with_search_filters_by_title(hedy_mocked) -> None:
    _, responses = hedy_mocked
    responses["/sessions"] = httpx.Response(
        200,
        json={
            "success": True,
            "data": [
                {"sessionId": "s1", "title": "Acme - Discovery", "startTime": "2026-05-10T09:00:00Z", "duration": 30},
                {"sessionId": "s2", "title": "Beta - Kickoff", "startTime": "2026-05-09T14:00:00Z", "duration": 30},
                {"sessionId": "s3", "title": "Acme - Followup", "startTime": "2026-05-08T11:00:00Z", "duration": 20},
            ],
            "pagination": {"hasMore": False},
        },
    )

    result = await hedy_service.list_sessions(limit=10, search="acme")

    assert [i.session_id for i in result.items] == ["s1", "s3"]


@pytest.mark.asyncio
async def test_get_session_prefers_cleaned_transcript(hedy_mocked) -> None:
    _, responses = hedy_mocked
    responses["/sessions/abc"] = httpx.Response(
        200,
        json={
            "sessionId": "abc",
            "title": "Acme - Discovery",
            "startTime": "2026-05-10T09:00:00Z",
            "transcript": "raw text",
            "cleaned_transcript": "polished text",
            "session_notes": "Pain points: legacy ERP",
        },
    )

    detail = await hedy_service.get_session("abc")

    assert detail.transcript == "polished text"
    assert detail.session_notes == "Pain points: legacy ERP"


@pytest.mark.asyncio
async def test_get_session_falls_back_to_raw_transcript(hedy_mocked) -> None:
    _, responses = hedy_mocked
    responses["/sessions/abc"] = httpx.Response(
        200,
        json={
            "sessionId": "abc",
            "title": "Acme",
            "startTime": "2026-05-10T09:00:00Z",
            "transcript": "raw text only",
            "session_notes": None,
        },
    )

    detail = await hedy_service.get_session("abc")

    assert detail.transcript == "raw text only"
    assert detail.session_notes is None


@pytest.mark.asyncio
async def test_get_session_propagates_upstream_404(hedy_mocked) -> None:
    _, responses = hedy_mocked
    responses["/sessions/nope"] = httpx.Response(404, json={"message": "not found"})

    with pytest.raises(hedy_service.HedyApiError) as excinfo:
        await hedy_service.get_session("nope")
    assert excinfo.value.status_code == 404


@pytest.mark.asyncio
async def test_unconfigured_client_raises_configerror(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hedy_service.settings, "hedy_api_key", "")
    monkeypatch.setattr(hedy_service, "_client", None)

    with pytest.raises(hedy_service.HedyConfigError):
        await hedy_service.list_sessions(limit=5)

"""Auth-gate smoke tests for the consultants endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_list_consultants_requires_auth() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/consultants")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_consultant_requires_auth() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/consultants",
            json={"name": "Max Mustermann", "titel": "Berater"},
        )
    assert response.status_code == 401

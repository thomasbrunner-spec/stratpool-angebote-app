"""Smoke tests for health endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_root() -> None:
    """Root endpoint returns app info."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_liveness() -> None:
    """Lightweight health check responds 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_hello_public() -> None:
    """Public hello does not require auth."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/hello/")
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_hello_authenticated_without_token() -> None:
    """Authenticated hello requires auth."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/hello/me")
    assert response.status_code == 401

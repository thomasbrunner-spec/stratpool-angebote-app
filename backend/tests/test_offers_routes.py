"""Auth-gate smoke tests for the offer list/detail/patch endpoints.

These do not hit the DB — they only verify that the routes are wired up and
require authentication. End-to-end DB tests live in the manual click-through
flow (Block 5b acceptance).
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_list_offers_requires_auth() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/offers")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_offer_requires_auth() -> None:
    fake_id = uuid.uuid4()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/offers/{fake_id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_patch_offer_requires_auth() -> None:
    fake_id = uuid.uuid4()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            f"/api/v1/offers/{fake_id}", json={"status": "sent"}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_render_offer_requires_auth() -> None:
    fake_id = uuid.uuid4()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/offers/{fake_id}/render")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_put_offer_content_requires_auth() -> None:
    fake_id = uuid.uuid4()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/offers/{fake_id}/content",
            json={"content": {}, "revision_notes": None},
        )
    assert response.status_code == 401

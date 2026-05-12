"""Auth + smoke tests for the prompts viewer endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.auth import AuthenticatedUser, get_current_user


@pytest.mark.asyncio
async def test_prompts_requires_auth() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/prompts")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_prompts_returns_full_body_for_authed_user() -> None:
    """Guards against signature drift in the helpers we call to render examples.

    The viewer calls offer_generator._build_user_message and
    render_via_skill._build_user_message with placeholder values; if either
    signature changes without updating prompts.py, this endpoint 500s in
    production (see Digest 4237420245, 2026-05-12).
    """
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id="00000000-0000-0000-0000-000000000000",
        email="test@example.com",
    )
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/prompts")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()

    gen = body["generate"]
    assert gen["model"] and gen["max_tokens"] > 0
    assert gen["system"] and gen["skeleton"]
    assert "<KUNDE>" in gen["user_message_example"]
    assert gen["user_message_notes"]

    rnd = body["render"]
    assert rnd["model"] and rnd["max_tokens"] > 0
    assert isinstance(rnd["betas"], list)
    assert set(rnd["skills"]) >= {"pptx_builtin", "word_builtin"}
    assert "<KUNDE>" in rnd["pptx_user_message_example"]
    assert "<KUNDE>" in rnd["word_user_message_example"]

"""
Anthropic API client wrapper.
"""

from anthropic import AsyncAnthropic
from loguru import logger

from app.config import get_settings

settings = get_settings()

_client: AsyncAnthropic | None = None


def get_anthropic_client() -> AsyncAnthropic:
    """Lazy singleton Anthropic client."""
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def health_check() -> dict[str, str | bool]:
    """
    Validate that the Anthropic API is reachable and our key works.
    Used in /health/anthropic endpoint.
    """
    client = get_anthropic_client()

    try:
        # Minimal API call: 1 token completion just to verify auth + connectivity
        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=10,
            messages=[{"role": "user", "content": "ping"}],
        )
        logger.debug(f"Anthropic health check OK: {response.id}")
        return {
            "ok": True,
            "model": settings.anthropic_model,
            "response_id": response.id,
        }
    except Exception as exc:
        logger.error(f"Anthropic health check failed: {exc}")
        return {"ok": False, "error": str(exc)}


async def simple_completion(prompt: str, max_tokens: int = 1024) -> str:
    """Simple completion helper for hello-world style demos."""
    client = get_anthropic_client()
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    # Extract text from first text block
    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts)

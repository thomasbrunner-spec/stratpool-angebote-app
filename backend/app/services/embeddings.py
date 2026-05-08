"""
Voyage AI client wrapper for embeddings.
"""

import voyageai
from loguru import logger

from app.config import get_settings

settings = get_settings()

_client: voyageai.AsyncClient | None = None


def get_voyage_client() -> voyageai.AsyncClient:
    """Lazy singleton Voyage client."""
    global _client
    if _client is None:
        _client = voyageai.AsyncClient(api_key=settings.voyage_api_key)
    return _client


async def embed_text(text: str, input_type: str = "document") -> list[float]:
    """
    Generate an embedding for a single text.

    Args:
        text: The text to embed
        input_type: "document" (for storage) or "query" (for search)

    Returns:
        List of floats representing the embedding (1024 dimensions for voyage-3-large)
    """
    client = get_voyage_client()
    result = await client.embed(
        texts=[text],
        model=settings.voyage_model,
        input_type=input_type,
    )
    return result.embeddings[0]


async def embed_texts(texts: list[str], input_type: str = "document") -> list[list[float]]:
    """Embed multiple texts in one batch call (more efficient)."""
    client = get_voyage_client()
    result = await client.embed(
        texts=texts,
        model=settings.voyage_model,
        input_type=input_type,
    )
    return result.embeddings


async def health_check() -> dict[str, str | bool | int]:
    """Validate Voyage API connectivity."""
    try:
        embedding = await embed_text("ping", input_type="document")
        logger.debug(f"Voyage health check OK, dimensions: {len(embedding)}")
        return {
            "ok": True,
            "model": settings.voyage_model,
            "dimensions": len(embedding),
        }
    except Exception as exc:
        logger.error(f"Voyage health check failed: {exc}")
        return {"ok": False, "error": str(exc)}

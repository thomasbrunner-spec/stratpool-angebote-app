"""
Health check endpoints.

These are critical for Coolify and for verifying that all integrations work.
"""

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import AsyncSessionLocal
from app.services import embeddings, llm

settings = get_settings()

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health() -> dict[str, str]:
    """Lightweight liveness probe — just checks the app is alive."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@router.get("/db")
async def health_db() -> dict[str, str | bool]:
    """Database connectivity check."""
    try:
        async with AsyncSessionLocal() as session:
            result: AsyncSession = await session.execute(text("SELECT 1"))
            value = result.scalar()
            return {"ok": value == 1, "database": "postgres"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.get("/anthropic")
async def health_anthropic() -> dict[str, str | bool]:
    """Anthropic API connectivity + auth check (uses ~5 tokens per call)."""
    return await llm.health_check()


@router.get("/voyage")
async def health_voyage() -> dict[str, str | bool | int]:
    """Voyage AI connectivity + auth check."""
    return await embeddings.health_check()


@router.get("/full")
async def health_full() -> dict:
    """Comprehensive health check across all integrations."""
    db_status = await health_db()
    anthropic_status = await health_anthropic()
    voyage_status = await health_voyage()

    all_ok = (
        db_status.get("ok", False)
        and anthropic_status.get("ok", False)
        and voyage_status.get("ok", False)
    )

    return {
        "ok": all_ok,
        "components": {
            "database": db_status,
            "anthropic": anthropic_status,
            "voyage": voyage_status,
        },
    }

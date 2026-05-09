"""Supabase Storage helpers for rendered Word/PPT artifacts.

The backend uploads with the service-role key (bypasses RLS), so the bucket
stays private and downloads happen via short-lived signed URLs.
"""

from __future__ import annotations

from supabase import AClient, acreate_client

from app.config import get_settings

_settings = get_settings()
_client: AClient | None = None


async def _get_client() -> AClient:
    """Cached async Supabase client (service-role)."""
    global _client
    if _client is None:
        _client = await acreate_client(
            _settings.supabase_url, _settings.supabase_service_role_key
        )
    return _client


async def upload_render(
    remote_path: str, content: bytes, content_type: str
) -> str:
    """Upload bytes to the render bucket. Overwrites if the path exists.

    Returns the storage key (= remote_path).
    """
    client = await _get_client()
    storage = client.storage.from_(_settings.render_storage_bucket)
    await storage.upload(
        path=remote_path,
        file=content,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    return remote_path


async def signed_url(remote_path: str, expires_in: int = 3600) -> str:
    """Generate a short-lived signed download URL for a stored object."""
    client = await _get_client()
    storage = client.storage.from_(_settings.render_storage_bucket)
    response = await storage.create_signed_url(remote_path, expires_in)
    return response["signedURL"]


def render_path(offer_id: str, version_number: int, suffix: str) -> str:
    """Canonical storage path: <offer_id>/v<n>/angebot.<suffix>"""
    return f"{offer_id}/v{version_number}/angebot.{suffix}"

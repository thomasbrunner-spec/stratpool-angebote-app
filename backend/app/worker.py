"""Arq worker for long-running offer-generation jobs.

The Anthropic streaming call routinely runs longer than the 60 s proxy
timeout (Coolify/Traefik) once max_tokens=32k. Doing it synchronously in
the request handler led to "fetch failed" errors even though the offer
was actually generated. The worker isolates the long-running work and
the request handler just enqueues + polls.

Job lifecycle:
  POST /offers/jobs/generate  -> enqueue, return job_id (immediate)
  worker picks up, runs generate_offer(), writes result to Redis
  GET /offers/jobs/{job_id}    -> queued | running | complete | failed
"""

from __future__ import annotations

import uuid

from arq.connections import RedisSettings
from loguru import logger

from app.config import get_settings
from app.db import AsyncSessionLocal
from app.schemas.offer import OfferGenerateRequest
from app.services.offer_generator import generate_offer

settings = get_settings()


async def generate_offer_job(
    ctx: dict,
    request_payload: dict,
    user_id: str | None,
) -> dict:
    """Worker entry: deserialize, run the pipeline, return JSON-safe dict.

    Inputs/outputs go through Arq's pickle serializer (default). Returning
    a plain dict keeps the result inspectable from any GET-job handler and
    avoids leaking Pydantic types across the worker/api boundary.
    """
    request = OfferGenerateRequest.model_validate(request_payload)
    parsed_user_id = uuid.UUID(user_id) if user_id else None
    logger.info(
        f"[worker] generate_offer_job start "
        f"job_id={ctx.get('job_id')} client={request.client_name!r}"
    )
    async with AsyncSessionLocal() as session:
        response = await generate_offer(request, parsed_user_id, session)
    logger.info(
        f"[worker] generate_offer_job done "
        f"job_id={ctx.get('job_id')} offer_id={response.offer_id}"
    )
    return response.model_dump(mode="json")


class WorkerSettings:
    """Arq worker configuration — `uv run arq app.worker.WorkerSettings`."""

    functions = [generate_offer_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    # Offer generation with max_tokens=32k can stream for several minutes.
    # Keep the per-job timeout generous, but bounded.
    job_timeout = 600
    # Keep results around long enough for the frontend to poll after the
    # user navigates away and comes back. 24h is plenty; the offer itself
    # is already persisted in Postgres.
    keep_result = 60 * 60 * 24
    max_jobs = 4

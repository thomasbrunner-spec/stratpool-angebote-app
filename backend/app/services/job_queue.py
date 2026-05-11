"""Arq job-queue access from the FastAPI side.

The worker process is defined in `app.worker`. This module is the thin
api-side wrapper: enqueue a job, look up its status. A single ArqRedis
pool is lazily created on first use and reused across requests.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from arq.connections import ArqRedis, RedisSettings, create_pool
from arq.jobs import Job
from arq.jobs import JobStatus as ArqJobStatus

from app.config import get_settings
from app.schemas.offer import (
    JobStatus,
    OfferGenerateRequest,
    OfferGenerateResponse,
    OfferJobStatusResponse,
)

settings = get_settings()

_pool: ArqRedis | None = None


async def get_pool() -> ArqRedis:
    """Lazily create and return a shared ArqRedis connection pool."""
    global _pool
    if _pool is None:
        _pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    return _pool


async def close_pool() -> None:
    """Close the pool — called from the FastAPI lifespan shutdown."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


async def enqueue_offer_generation(
    request: OfferGenerateRequest,
    user_id: uuid.UUID | None,
) -> str:
    """Enqueue a generate_offer_job and return its job_id."""
    pool = await get_pool()
    job = await pool.enqueue_job(
        "generate_offer_job",
        request.model_dump(mode="json"),
        str(user_id) if user_id else None,
    )
    if job is None:
        # arq returns None when a job with the same id already exists; we
        # don't pass an id, so this shouldn't happen — but guard for it.
        raise RuntimeError("Failed to enqueue offer-generation job")
    return job.job_id


_STATUS_MAP: dict[ArqJobStatus, JobStatus] = {
    ArqJobStatus.deferred: "queued",
    ArqJobStatus.queued: "queued",
    ArqJobStatus.in_progress: "running",
    ArqJobStatus.complete: "complete",  # may flip to "failed" below
    ArqJobStatus.not_found: "not_found",
}


async def get_offer_job_status(job_id: str) -> OfferJobStatusResponse:
    """Look up a job's status and (if finished) materialise its result.

    For finished jobs we read via `result_info()` instead of `result()` so a
    worker exception surfaces as a structured `error` field rather than
    re-raising into the request handler.
    """
    pool = await get_pool()
    job = Job(job_id, redis=pool)

    arq_status = await job.status()
    status: JobStatus = _STATUS_MAP.get(arq_status, "not_found")

    enqueue_time: datetime | None = None
    start_time: datetime | None = None
    finish_time: datetime | None = None
    result_payload: OfferGenerateResponse | None = None
    error: str | None = None

    if arq_status == ArqJobStatus.complete:
        # result_info returns a JobResult (subclass of JobDef) with success +
        # result/exception + timing. Does not block, does not re-raise.
        job_result = await job.result_info()
        if job_result is not None:
            enqueue_time = job_result.enqueue_time
            start_time = job_result.start_time
            finish_time = job_result.finish_time
            if job_result.success and isinstance(job_result.result, dict):
                result_payload = OfferGenerateResponse.model_validate(job_result.result)
            else:
                status = "failed"
                raw = job_result.result
                if isinstance(raw, BaseException):
                    error = f"{type(raw).__name__}: {raw}"
                else:
                    error = f"Unexpected worker result: {raw!r}"
        else:
            # Status said "complete" but the result expired between calls —
            # treat it as not_found so the frontend can show a clean error.
            status = "not_found"
    else:
        info = await job.info()
        if info is not None:
            enqueue_time = info.enqueue_time

    return OfferJobStatusResponse(
        job_id=job_id,
        status=status,
        enqueue_time=enqueue_time,
        start_time=start_time,
        finish_time=finish_time,
        result=result_payload,
        error=error,
    )

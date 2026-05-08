"""Top-K cosine retrieval over `offer_embeddings` for few-shot generation.

Each retrieved row carries the latest OfferVersion (by version_number) so the
caller can render its `content_json` as a few-shot example without a second
round-trip.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Offer, OfferEmbedding, OfferVersion

# The baseline migration created the IVFFLAT index with lists=100 — defensible
# at scale, but with a tiny pool (5–50 offers) most clusters are empty and the
# default probes=1 returns 0 rows. probes=100 == exact search for our pool.
_IVFFLAT_PROBES = 100


@dataclass(frozen=True)
class RetrievedOffer:
    """One similarity hit. `score` is cosine similarity in [0, 1+]."""

    offer: Offer
    latest_version: OfferVersion
    score: float


async def retrieve_similar_offers(
    session: AsyncSession,
    query_embedding: list[float],
    k: int = 3,
    exclude_offer_ids: list[uuid.UUID] | None = None,
) -> list[RetrievedOffer]:
    """Return up to `k` offers ranked by cosine similarity, descending.

    pgvector's `cosine_distance` returns 1 - cos_sim, so we order ascending
    and convert back to similarity in the result.
    """
    await session.execute(text(f"SET LOCAL ivfflat.probes = {_IVFFLAT_PROBES}"))

    distance = OfferEmbedding.embedding.cosine_distance(query_embedding).label("distance")

    stmt = (
        select(OfferEmbedding.offer_id, distance)
        .order_by(distance.asc())
        .limit(k)
    )
    if exclude_offer_ids:
        stmt = stmt.where(OfferEmbedding.offer_id.notin_(exclude_offer_ids))

    rows = (await session.execute(stmt)).all()
    if not rows:
        return []

    offer_ids = [row.offer_id for row in rows]
    distances = {row.offer_id: row.distance for row in rows}

    offers = (
        (
            await session.execute(
                select(Offer)
                .where(Offer.id.in_(offer_ids))
                .options(selectinload(Offer.versions))
            )
        )
        .scalars()
        .all()
    )

    results: list[RetrievedOffer] = []
    for offer in offers:
        if not offer.versions:
            continue
        latest = max(offer.versions, key=lambda v: v.version_number)
        results.append(
            RetrievedOffer(
                offer=offer,
                latest_version=latest,
                score=1.0 - float(distances[offer.id]),
            )
        )

    results.sort(key=lambda r: r.score, reverse=True)
    return results

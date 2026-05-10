"""Top-K cosine retrieval over `knowledge_chunks`.

Returns curated reference material (Kompendium chapters etc.) so the
generate pipeline can ground the offer in real methodology instead of
producing generic boilerplate.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KnowledgeChunk

# Same reasoning as retrieval.retrieve_similar_offers: the IVFFLAT index
# has lists=100; for a bounded corpus, probes=100 is exact search and
# safe.
_IVFFLAT_PROBES = 100

# Chunks are typically ~800-1500 tokens. K=4 gives the model ~5k tokens
# of curated reference, which is meaningful but doesn't dominate the
# input budget.
DEFAULT_K = 4


@dataclass(frozen=True)
class RetrievedKnowledge:
    chunk: KnowledgeChunk
    score: float  # cosine similarity in [0, 1+]


async def retrieve_knowledge(
    session: AsyncSession,
    query_embedding: list[float],
    k: int = DEFAULT_K,
    source: str | None = None,
) -> list[RetrievedKnowledge]:
    """Return up to `k` knowledge chunks ranked by cosine similarity, descending."""
    await session.execute(text(f"SET LOCAL ivfflat.probes = {_IVFFLAT_PROBES}"))

    distance = KnowledgeChunk.embedding.cosine_distance(query_embedding).label("distance")

    stmt = select(KnowledgeChunk, distance).order_by(distance.asc()).limit(k)
    if source:
        stmt = stmt.where(KnowledgeChunk.source == source)

    rows = (await session.execute(stmt)).all()
    return [
        RetrievedKnowledge(chunk=chunk, score=1.0 - float(distance))
        for chunk, distance in rows
    ]


def render_knowledge_block(items: list[RetrievedKnowledge]) -> str:
    """Format the retrieved chunks as a markdown reference block."""
    if not items:
        return ""
    lines = ["## Domänen-Wissen aus dem Kompendium (zur fachlichen Substanz nutzen, nicht zitieren)\n"]
    for r in items:
        c = r.chunk
        header_parts = []
        if c.chapter:
            header_parts.append(c.chapter)
        if c.title and c.title != c.chapter:
            header_parts.append(c.title)
        header = " — ".join(header_parts) if header_parts else f"Auszug {c.ord}"
        lines.append(f"### {header} (sim={r.score:.2f})\n")
        lines.append(c.text.strip())
        lines.append("")
    return "\n".join(lines)

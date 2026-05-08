"""Seed historical offers from bestandsangebote.yaml into the DB.

For each offer entry the script:
  1. Extracts the source file (DOCX/PDF/PPTX) to Markdown.
  2. Applies the per-entry redact mapping to scrub PII.
  3. Computes a Voyage embedding from the anonymized text.
  4. Upserts offers + offer_versions + offer_embeddings idempotently
     (existing rows with the same client_name are deleted and re-created).

Run:
    # Tunnel must be up (see CLAUDE.md "Lokale DB-Verbindung")
    cd backend
    uv run --group seed python -m scripts.seed_bestandsangebote
"""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from loguru import logger
from sqlalchemy import delete, select

from app.db import AsyncSessionLocal
from app.models import Offer, OfferEmbedding, OfferVersion
from app.services.embeddings import embed_text
from scripts.anonymize import anonymize
from scripts.extract import extract

VALID_STATUSES = {"draft", "sent", "won", "lost"}
VALID_CONSULTING_TYPES = {"ki_strategie", "ai_design_sprint", "prozessberatung", "workshop"}


def _yaml_path() -> Path:
    return Path(__file__).resolve().parent.parent / "seeds" / "bestandsangebote.yaml"


def _validate(entry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    slug = entry.get("slug", "<no-slug>")
    if not entry.get("client_name"):
        errors.append(f"[{slug}] client_name missing")
    if entry.get("status") not in VALID_STATUSES:
        errors.append(
            f"[{slug}] status={entry.get('status')!r} not in {sorted(VALID_STATUSES)}"
        )
    if entry.get("consulting_type") not in VALID_CONSULTING_TYPES:
        errors.append(
            f"[{slug}] consulting_type={entry.get('consulting_type')!r} "
            f"not in {sorted(VALID_CONSULTING_TYPES)}"
        )
    if entry.get("price_eur") is None:
        errors.append(f"[{slug}] price_eur is null")
    src = entry.get("source_file")
    if not src or not Path(src).exists():
        errors.append(f"[{slug}] source_file missing or unreadable: {src!r}")
    return errors


async def _seed() -> None:
    yaml_path = _yaml_path()
    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    entries: list[dict[str, Any]] = data.get("offers", [])
    if not entries:
        logger.error("No offers found in YAML — aborting.")
        sys.exit(1)

    all_errors: list[str] = []
    for entry in entries:
        all_errors.extend(_validate(entry))
    if all_errors:
        logger.error("Validation failed — fill the YAML and re-run:")
        for e in all_errors:
            logger.error(f"  {e}")
        sys.exit(1)

    client_names = [e["client_name"] for e in entries]

    async with AsyncSessionLocal() as session:
        # Idempotency: delete existing offers with the same client_names.
        # Cascades drop offer_versions + offer_embeddings.
        deleted = await session.execute(
            delete(Offer).where(Offer.client_name.in_(client_names))
        )
        if deleted.rowcount:
            logger.info(f"Removed {deleted.rowcount} existing offer(s) before reseeding.")

        for entry in entries:
            slug = entry["slug"]
            logger.info(f"[{slug}] extracting {Path(entry['source_file']).name}")
            raw_md = extract(Path(entry["source_file"]))
            redact_map: dict[str, str] = entry.get("redact") or {}
            anonymized = anonymize(raw_md, redact_map)

            logger.info(f"[{slug}] embedding ({len(anonymized)} chars)")
            vector = await embed_text(anonymized)

            offer = Offer(
                client_name=entry["client_name"],
                industry=entry.get("industry"),
                consulting_type=entry["consulting_type"],
                status=entry["status"],
                price_eur=Decimal(str(entry["price_eur"])),
            )
            session.add(offer)
            await session.flush()

            session.add(
                OfferVersion(
                    offer_id=offer.id,
                    version_number=1,
                    content_json={
                        "format": "legacy_markdown",
                        "source_slug": slug,
                        "markdown": anonymized,
                    },
                )
            )
            session.add(
                OfferEmbedding(
                    offer_id=offer.id,
                    embedding=vector,
                    summary=anonymized,
                )
            )
            logger.info(f"[{slug}] queued offer {offer.id}")

        await session.commit()

        # Verification: count rows for the seeded client_names.
        rows = (
            await session.execute(
                select(Offer.client_name, Offer.id).where(
                    Offer.client_name.in_(client_names)
                )
            )
        ).all()
        logger.info(f"Seed complete — {len(rows)} offers in DB:")
        for name, oid in rows:
            logger.info(f"  {name}  {oid}")


def main() -> None:
    asyncio.run(_seed())


if __name__ == "__main__":
    main()

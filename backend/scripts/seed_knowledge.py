"""Seed knowledge_chunks from a PDF (e.g. the KISB Kompendium).

Pipeline:
  1. Read PDF pages, drop the obvious header/footer noise.
  2. Detect section boundaries via heuristics on numbered chapter
     headings ("^\d+\s+\w+", "^\d+\.\d+\s+\w+").
  3. Pack pages into rolling chunks of ~1200 tokens (Voyage's sweet
     spot for retrieval-quality vs. context budget).
  4. Embed with Voyage `voyage-3-large`, input_type="document".
  5. UPSERT into knowledge_chunks (delete existing rows for that
     `source` first, so re-runs are idempotent).

Run locally with the SSH tunnel up:
    cd backend
    uv sync --group seed
    uv run python -m scripts.seed_knowledge \
        --source "kisb_kompendium" \
        --pdf "/Users/.../KISB_Kompendium_20251020.pdf"
"""

from __future__ import annotations

import argparse
import asyncio
import re
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger
from pypdf import PdfReader
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.services.embeddings import embed_text

settings = get_settings()

# Heuristic: Voyage's 1024-dim model retrieves best with chunks ~800-1500 tokens.
# 1 token ≈ 4 chars in German -> aim for ~5000 chars hard, ~3500 chars soft.
SOFT_CHARS = 3500
HARD_CHARS = 6000
OVERLAP_CHARS = 400  # carry the tail of chunk N into chunk N+1 for context bleed

# Lines that match these are noise (page header/footer in the Kompendium PDF).
_NOISE_PATTERNS = [
    re.compile(r"^\s*KOERTING-INSTITUTE\.com\s*$", re.I),
    re.compile(r"^\s*KI-STRATEGIEBERATER\s*$", re.I),
    re.compile(r"^\s*Das vollständige Kompendium\s*$", re.I),
    re.compile(r"^\s*-\s*\d+\s*-\s*$"),  # "- 12 -"
]

_CHAPTER_RE = re.compile(r"^(?P<num>\d+(?:\.\d+)?)\s+(?P<title>[A-ZÄÖÜ].+?)\s*$")


@dataclass
class PageBlock:
    page: int
    text: str  # cleaned multi-line text


@dataclass
class Section:
    chapter: str | None
    title: str | None
    page_from: int
    page_to: int
    text: str = ""
    pages: list[int] = field(default_factory=list)


def _is_noise(line: str) -> bool:
    return any(pat.match(line) for pat in _NOISE_PATTERNS)


def _clean_page(raw: str) -> str:
    # PDF extract sometimes carries NUL bytes and other control chars
    # that Postgres rejects under UTF8. Strip them before line-level work.
    raw = raw.replace("\x00", "")
    raw = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", raw)
    out: list[str] = []
    for raw_line in raw.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            out.append("")
            continue
        if _is_noise(line):
            continue
        out.append(line)
    # collapse 3+ blank lines into 2
    cleaned = "\n".join(out)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _read_pdf(path: Path) -> list[PageBlock]:
    reader = PdfReader(str(path))
    blocks: list[PageBlock] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            raw = page.extract_text() or ""
        except Exception as e:
            logger.warning(f"page {i}: extract_text failed ({e}), skipping")
            continue
        cleaned = _clean_page(raw)
        if not cleaned:
            continue
        blocks.append(PageBlock(page=i, text=cleaned))
    return blocks


def _detect_sections(blocks: list[PageBlock]) -> list[Section]:
    """Group consecutive pages under section headers.

    The heuristic finds the first header on a page (line that looks like
    `1 Foo` or `2.3 Bar`) and treats that as the start of a new section.
    """
    sections: list[Section] = []
    current = Section(chapter=None, title=None, page_from=blocks[0].page, page_to=blocks[0].page)
    for blk in blocks:
        first_lines = [ln for ln in blk.text.splitlines()[:5] if ln.strip()]
        new_chapter: tuple[str, str] | None = None
        for ln in first_lines:
            m = _CHAPTER_RE.match(ln)
            if m:
                num = m.group("num")
                title = m.group("title").strip()
                # Filter ToC noise: chapter line must be short-ish, no dots/page-numbers
                if "..." not in title and len(title) < 80 and not title.endswith(tuple("0123456789")):
                    new_chapter = (num, title)
                    break
        if new_chapter:
            if current.text:
                sections.append(current)
            current = Section(
                chapter=new_chapter[0],
                title=new_chapter[1],
                page_from=blk.page,
                page_to=blk.page,
            )
        current.pages.append(blk.page)
        current.page_to = blk.page
        current.text = (current.text + "\n\n" + blk.text).strip() if current.text else blk.text

    if current.text:
        sections.append(current)
    return sections


@dataclass
class Chunk:
    ord: int
    section: Section
    text: str


def _split_section(section: Section, start_ord: int) -> list[Chunk]:
    """Split a section's text into chunks of ~SOFT_CHARS, never exceeding HARD_CHARS."""
    text = section.text.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    cursor = 0
    ord_ = start_ord
    while cursor < len(text):
        end = min(cursor + SOFT_CHARS, len(text))
        # Try to break at a paragraph boundary close to the soft limit.
        if end < len(text):
            tail = text[cursor:end + 200]
            # last "\n\n" in window
            break_at = tail.rfind("\n\n")
            if break_at == -1 or break_at < SOFT_CHARS // 2:
                # fall back to last sentence end
                break_at = max(tail.rfind(". "), tail.rfind("! "), tail.rfind("? "))
            if break_at == -1 or break_at < SOFT_CHARS // 2:
                # hard cut
                break_at = SOFT_CHARS
            end = min(cursor + break_at + 1, len(text))
        # never exceed HARD_CHARS
        end = min(end, cursor + HARD_CHARS)
        piece = text[cursor:end].strip()
        if piece:
            chunks.append(Chunk(ord=ord_, section=section, text=piece))
            ord_ += 1
        if end >= len(text):
            break
        cursor = max(cursor + 1, end - OVERLAP_CHARS)
    return chunks


def _build_chunks(sections: list[Section]) -> list[Chunk]:
    chunks: list[Chunk] = []
    ord_counter = 0
    for sec in sections:
        out = _split_section(sec, start_ord=ord_counter)
        chunks.extend(out)
        ord_counter += len(out)
    return chunks


async def _seed(source: str, pdf: Path, dry_run: bool) -> None:
    blocks = _read_pdf(pdf)
    logger.info(f"PDF: {len(blocks)} non-empty pages")
    sections = _detect_sections(blocks)
    logger.info(f"detected {len(sections)} sections")
    chunks = _build_chunks(sections)
    logger.info(f"built {len(chunks)} chunks (avg ~{sum(len(c.text) for c in chunks) // max(1,len(chunks))} chars)")

    if dry_run:
        for c in chunks[:3]:
            logger.info(
                f"--- chunk {c.ord} (chapter={c.section.chapter} title={c.section.title!r}, "
                f"pages={c.section.page_from}-{c.section.page_to}, {len(c.text)} chars) ---\n"
                f"{c.text[:400]}…\n"
            )
        return

    # Embed all chunks. Voyage handles batching internally up to its limits;
    # we fire one call per chunk to keep the code simple — corpus is bounded.
    logger.info(f"embedding {len(chunks)} chunks via Voyage…")
    embeddings: list[list[float]] = []
    for i, c in enumerate(chunks):
        emb = await embed_text(c.text, input_type="document")
        embeddings.append(emb)
        if (i + 1) % 10 == 0:
            logger.info(f"  embedded {i + 1}/{len(chunks)}")

    # Persist. Replace existing rows for the same source.
    # `app.db` does the same scheme rewrite — DATABASE_URL is stored with the
    # plain `postgresql://` scheme so psycopg2 can read it for sync access,
    # async needs `+asyncpg`.
    db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM knowledge_chunks WHERE source = :src"),
            {"src": source},
        )
        for c, emb in zip(chunks, embeddings, strict=True):
            await conn.execute(
                text(
                    """
                    INSERT INTO knowledge_chunks
                        (source, chapter, title, page_from, page_to, ord, text, token_count, embedding)
                    VALUES
                        (:source, :chapter, :title, :page_from, :page_to, :ord, :text, :token_count, :embedding)
                    """
                ),
                {
                    "source": source,
                    "chapter": c.section.chapter,
                    "title": c.section.title,
                    "page_from": c.section.page_from,
                    "page_to": c.section.page_to,
                    "ord": c.ord,
                    "text": c.text,
                    "token_count": len(c.text) // 4,  # rough estimate
                    "embedding": str(emb),  # pgvector accepts the textual array literal
                },
            )
    await engine.dispose()
    logger.info(f"persisted {len(chunks)} chunks under source={source!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="logical source tag, e.g. kisb_kompendium")
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.pdf.exists():
        raise SystemExit(f"PDF not found: {args.pdf}")

    asyncio.run(_seed(args.source, args.pdf, args.dry_run))


if __name__ == "__main__":
    main()

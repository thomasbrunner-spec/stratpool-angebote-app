"""Phase-1 smoke test for the Anthropic Code-Execution + Skills pipeline.

Sends a tiny discovery prompt to Claude with:
  - the custom era-presentation skill loaded into the container
  - the built-in `pptx` skill (so python-pptx is set up)
  - the code_execution tool

The script then walks the response, finds the .pptx file Claude wrote in the
container, downloads it via the Files API, and saves it locally for visual
inspection.

Usage:
    cd backend
    uv run python -m scripts.test_skill_pptx
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import anthropic

from app.config import get_settings

settings = get_settings()

SKILL_ID = os.environ.get("ERA_PRESENTATION_SKILL_ID") or "skill_01DNwzRKHaHjgnNXuNLKjDWR"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / ".local" / "phase1_smoke.pptx"

USER_PROMPT = """Erstelle ein KURZES ERA-Präsentation-Deck für ein Test-Angebot.

## Kundendaten
Kunde: TestKunde GmbH
Beratungsart: KI-Strategie
Discovery-Notiz: TestKunde will Use-Cases priorisieren, hat keine konkrete Roadmap.

## Berater (zwei Personen)
Hauptberater (Overlay-Box rechts unten):
  Name: Thomas Brunner
  Titel: Senior Partner
  Tel: +49 160 7155999
  E-Mail: tbrunner@eragroup.com

Co-Berater (Layout-Block links unten — überschreibe `text1111` etc.):
  Name: Michael Paulus
  Titel: Senior Partner
  Tel: +49 160 0000000
  E-Mail: mpaulus@eragroup.com

## Folien-Auftrag
1. Cover-Folie: Beide Berater nebeneinander auf gleicher Y-Höhe (siehe Skill-Sektion "Zwei Berater auf der Titelfolie"), Kundenname linksbündig zu "Für:".
2. Eine zweite Folie mit Layout "1 x Content", Title "Ausgangslage TestKunde" und einem Absatz dazu (Body-Text REGULAR, nicht fett).

Das wars — keine weiteren Folien. Nutze den era-presentation Skill für die ERA-CI."""


def _iter_file_ids(response):
    """Yield every file_id surfaced by any *_code_execution_tool_result block."""
    for block in response.content:
        btype = getattr(block, "type", "")
        if not btype.endswith("_tool_result"):
            continue
        inner = getattr(block, "content", None)
        if inner is None:
            continue
        # Could be an error block or a result block
        items = getattr(inner, "content", None)
        if items is None:
            continue
        for output in items:
            fid = getattr(output, "file_id", None)
            if fid:
                yield btype, fid


def _save_first_pptx(response, client: anthropic.Anthropic) -> Path | None:
    """Walk every tool result, download each file_id, save the first valid pptx."""
    for source, fid in _iter_file_ids(response):
        print(f"  → from {source}: downloading {fid}")
        try:
            data = client.beta.files.download(
                fid, betas=["files-api-2025-04-14"]
            ).read()
        except Exception as exc:
            print(f"    download failed: {exc}")
            continue
        if data[:2] != b"PK":
            print(f"    skipping non-zip ({len(data)} bytes)")
            continue
        OUTPUT_PATH.parent.mkdir(exist_ok=True)
        OUTPUT_PATH.write_bytes(data)
        print(f"    saved {len(data):,} bytes → {OUTPUT_PATH}")
        return OUTPUT_PATH
    return None


def main() -> None:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    print(f"Custom skill_id: {SKILL_ID}")
    print(f"Calling Claude (this can take 30–90s)...\n")

    t0 = time.time()
    response = client.beta.messages.create(
        model=settings.anthropic_model,
        max_tokens=16384,
        container={
            "skills": [
                {"skill_id": "pptx", "type": "anthropic", "version": "latest"},
                {"skill_id": SKILL_ID, "type": "custom", "version": "latest"},
            ],
        },
        tools=[{"type": "code_execution_20260120", "name": "code_execution"}],
        messages=[{"role": "user", "content": USER_PROMPT}],
        betas=[
            "skills-2025-10-02",
            "code-execution-2025-05-22",
            "files-api-2025-04-14",
        ],
    )
    dt = time.time() - t0
    print(f"...done in {dt:.1f}s\n")

    print(f"stop_reason: {response.stop_reason}")
    print(f"usage: input={response.usage.input_tokens} output={response.usage.output_tokens}")
    print(f"content blocks: {len(response.content)}")
    for i, block in enumerate(response.content):
        kind = getattr(block, "type", "?")
        print(f"  [{i}] {kind}")

    saved = _save_first_pptx(response, client)
    if saved is None:
        print("\nNo .pptx file in the response. Dumping last text blocks for diagnostics:")
        for block in response.content[-3:]:
            if getattr(block, "type", None) == "text":
                print(block.text[:500])
        sys.exit(1)


if __name__ == "__main__":
    main()

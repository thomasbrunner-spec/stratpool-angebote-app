"""Diagnose run for the Word render path. Logs every block in the response
so we can see what the docx skill actually did and what tool Claude invoked.
"""

from __future__ import annotations

import json
import os
import time

import anthropic

from app.config import get_settings

settings = get_settings()

USER_PROMPT = """Erstelle ein KURZES ERA-Word-Dokument als Test.

## Berater
- Name: Thomas Brunner
- Titel: Senior Partner
- Tel: +49 160 7155999
- E-Mail: tbrunner@eragroup.com

## Mandat
- Kunde: TestKunde GmbH
- Discovery: TestKunde will Use-Cases priorisieren.

## Auftrag
- Titelseite mit Logo + Kundenname.
- Eine Seite "Ausgangslage" mit kurzem Absatz.
- Speichere unter `/home/claude/angebot.docx`.

Nutze den era-word Skill für ERA-CI und python-docx für das Rendering."""


def main() -> None:
    skill_id = os.environ.get(
        "ERA_WORD_SKILL_ID", settings.era_word_skill_id
    )
    if not skill_id:
        raise SystemExit("ERA_WORD_SKILL_ID is not configured")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    pre_files = {
        f.id
        for f in client.beta.files.list(limit=100, betas=["files-api-2025-04-14"]).data
    }
    print(f"pre_files count: {len(pre_files)}")

    t0 = time.time()
    response = client.beta.messages.create(
        model="claude-opus-4-7",
        max_tokens=16384,
        container={
            "skills": [
                {"skill_id": "docx", "type": "anthropic", "version": "latest"},
                {"skill_id": skill_id, "type": "custom", "version": "latest"},
            ],
        },
        tools=[{"type": "code_execution_20260120", "name": "code_execution"}],
        messages=[{"role": "user", "content": USER_PROMPT}],
        betas=["skills-2025-10-02", "code-execution-2025-05-22", "files-api-2025-04-14"],
    )
    print(f"\n=== response in {time.time() - t0:.1f}s ===")
    print(f"stop_reason: {response.stop_reason}")
    print(f"usage: in={response.usage.input_tokens} out={response.usage.output_tokens}")
    print(f"content blocks: {len(response.content)}\n")

    for i, block in enumerate(response.content):
        kind = getattr(block, "type", "?")
        print(f"--- block [{i}] type={kind}")
        # Dump useful fields per block type
        if kind == "text":
            text = block.text  # type: ignore
            print(text[:600])
            if len(text) > 600:
                print(f"... ({len(text) - 600} more chars)")
        else:
            try:
                d = block.model_dump()  # type: ignore
            except Exception:
                d = {}
            # Truncate big strings
            stripped = json.dumps(d, default=str)[:800]
            print(stripped)

    print("\n--- new files in workspace ---")
    post = client.beta.files.list(limit=100, betas=["files-api-2025-04-14"]).data
    new = [f for f in post if f.id not in pre_files]
    new.sort(key=lambda f: f.created_at, reverse=True)
    for f in new:
        print(f"  {f.created_at}  {f.id}  size={f.size_bytes:>10,}B  {f.mime_type[:40]:40}  {f.filename!r}")


if __name__ == "__main__":
    main()

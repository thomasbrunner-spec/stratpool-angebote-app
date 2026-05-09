"""Upload reference offer PPTs to Anthropic Files API and print the file_ids.

These files become Claude's few-shot pool when rendering a new offer: each
generation can refer to them via container_upload blocks so Claude sees the
real reference decks (style, slide flow, density) before composing.

Run once. Save the output as FEW_SHOT_FILE_IDS in .env (comma-separated).
Re-run if the reference set changes — Anthropic charges per file storage,
but it's negligible at this scale.

Usage:
    cd backend
    uv run python -m scripts.upload_few_shots
"""

from __future__ import annotations

import sys
from pathlib import Path

import anthropic

from app.config import get_settings

settings = get_settings()

_REFERENCE_DIR = Path(__file__).resolve().parent.parent / ".local"
_PPTX_MIME = (
    "application/vnd.openxmlformats-officedocument.presentationml.presentation"
)


def main() -> None:
    candidates = sorted(_REFERENCE_DIR.glob("ERA_Projektskizze_*.pptx"))
    if not candidates:
        sys.exit(
            f"No reference PPTs found in {_REFERENCE_DIR} matching "
            "ERA_Projektskizze_*.pptx"
        )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    print(f"Uploading {len(candidates)} reference PPTs...\n")

    file_ids: list[str] = []
    for path in candidates:
        size = path.stat().st_size
        print(f"  → {path.name}  ({size:,} B)")
        with open(path, "rb") as f:
            metadata = client.beta.files.upload(
                file=(path.name, f, _PPTX_MIME),
                betas=["files-api-2025-04-14"],
            )
        print(f"    {metadata.id}  filename={metadata.filename!r}")
        file_ids.append(metadata.id)

    print()
    print("Add this to backend/.env and the root .env:")
    print(f"  FEW_SHOT_FILE_IDS={','.join(file_ids)}")


if __name__ == "__main__":
    main()

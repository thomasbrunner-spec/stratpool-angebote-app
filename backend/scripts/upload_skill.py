"""Upload the era-presentation skill to Anthropic and print the skill_id.

Run once (or after the skill content changes). The resulting skill_id should
be saved as ERA_PRESENTATION_SKILL_ID in .env so the generation pipeline can
reference it.

Usage:
    cd backend
    uv run python -m scripts.upload_skill
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import anthropic

from app.config import get_settings

settings = get_settings()

# Skill source: the in-repo skill (we evolve it independently of the
# claude.ai mirror). On first upload Anthropic returns a fresh skill_id.
_SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "era-presentation"
_SKILL_MD = _SKILL_DIR / "SKILL.md"
_TEMPLATE = _SKILL_DIR / "assets" / "ERA_Template.pptx"

_PPTX_MIME = (
    "application/vnd.openxmlformats-officedocument.presentationml.presentation"
)


def main() -> None:
    if not _SKILL_MD.exists():
        sys.exit(f"SKILL.md not found at {_SKILL_MD}")
    if not _TEMPLATE.exists():
        sys.exit(f"ERA_Template.pptx not found at {_TEMPLATE}")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    existing_id = os.environ.get("ERA_PRESENTATION_SKILL_ID")
    print(f"SKILL.md: {_SKILL_MD.stat().st_size:,} B")
    print(f"Template: {_TEMPLATE.stat().st_size:,} B")
    print(f"Existing ERA_PRESENTATION_SKILL_ID: {existing_id or '(none)'}")
    print()

    # All files must live in a single top-level folder; SKILL.md must be at
    # the root of that folder. Anthropic enforces this strictly.
    with open(_SKILL_MD, "rb") as md, open(_TEMPLATE, "rb") as tmpl:
        files = [
            ("era-presentation/SKILL.md", md, "text/markdown"),
            ("era-presentation/assets/ERA_Template.pptx", tmpl, _PPTX_MIME),
        ]
        if existing_id:
            print(f"Creating new VERSION of {existing_id}...")
            version = client.beta.skills.versions.create(
                existing_id,
                files=files,
                betas=["skills-2025-10-02"],
            )
            print(f"\nNew version created.")
            print(f"  skill_id: {existing_id}  (unchanged)")
            print(f"  version:  {version.version}")
            print(f"  Container can keep using version='latest'.")
        else:
            print("No existing skill_id — creating a fresh skill...")
            skill = client.beta.skills.create(
                display_title="ERA Group Präsentation",
                files=files,
                betas=["skills-2025-10-02"],
            )
            print(f"\nSkill created.")
            print(f"  id:             {skill.id}")
            print(f"  latest_version: {skill.latest_version!r}")
            print()
            print(f"Add this to backend/.env and the root .env:")
            print(f"  ERA_PRESENTATION_SKILL_ID={skill.id}")


if __name__ == "__main__":
    main()

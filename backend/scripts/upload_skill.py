"""Upload era-* skills to Anthropic.

Usage:
    cd backend
    uv run python -m scripts.upload_skill                # uploads era-presentation
    uv run python -m scripts.upload_skill era-word       # uploads era-word
    uv run python -m scripts.upload_skill all            # uploads both

If the matching env var (ERA_PRESENTATION_SKILL_ID / ERA_WORD_SKILL_ID) is set,
a new VERSION of the existing skill is created. Otherwise a fresh skill is
created and the script prints the line you need to paste into both .env files.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import anthropic

from app.config import get_settings

settings = get_settings()

_SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"
_PPTX_MIME = (
    "application/vnd.openxmlformats-officedocument.presentationml.presentation"
)


@dataclass
class SkillSpec:
    """Describes one local skill bundle and how to upload it."""

    name: str  # directory name under backend/skills/, also the prefix used by Anthropic
    display_title: str
    env_var: str
    files: list[tuple[str, str]]  # (relative path inside skill dir, mime type)


_SPECS: dict[str, SkillSpec] = {
    "era-presentation": SkillSpec(
        name="era-presentation",
        display_title="ERA Group Präsentation",
        env_var="ERA_PRESENTATION_SKILL_ID",
        files=[
            ("SKILL.md", "text/markdown"),
            ("assets/ERA_Template.pptx", _PPTX_MIME),
        ],
    ),
    "era-word": SkillSpec(
        name="era-word",
        display_title="ERA Group Word",
        env_var="ERA_WORD_SKILL_ID",
        files=[
            ("SKILL.md", "text/markdown"),
            ("assets/era_logo.png", "image/png"),
        ],
    ),
}


def _upload(spec: SkillSpec) -> None:
    skill_dir = _SKILLS_ROOT / spec.name
    if not skill_dir.is_dir():
        sys.exit(f"Skill directory not found: {skill_dir}")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    existing_id = os.environ.get(spec.env_var)

    print(f"=== {spec.name} ===")
    print(f"  display_title: {spec.display_title!r}")
    print(f"  Existing {spec.env_var}: {existing_id or '(none)'}")

    # Open files; remember to close them after the API call.
    open_files = []
    try:
        api_files: list[tuple[str, object, str]] = []
        for rel, mime in spec.files:
            local_path = skill_dir / rel
            if not local_path.exists():
                sys.exit(f"Missing file: {local_path}")
            f = open(local_path, "rb")
            open_files.append(f)
            print(f"  → {rel}: {local_path.stat().st_size:,} B")
            api_files.append((f"{spec.name}/{rel}", f, mime))

        if existing_id:
            print(f"  Creating new version of {existing_id}…")
            version = client.beta.skills.versions.create(
                existing_id, files=api_files, betas=["skills-2025-10-02"]
            )
            print(f"  ✓ new version: {version.version}")
        else:
            print("  No existing skill_id — creating fresh skill…")
            skill = client.beta.skills.create(
                display_title=spec.display_title,
                files=api_files,
                betas=["skills-2025-10-02"],
            )
            print(f"  ✓ skill_id: {skill.id}")
            print()
            print("  Add this to backend/.env and the root .env:")
            print(f"    {spec.env_var}={skill.id}")
    finally:
        for f in open_files:
            f.close()


def main() -> None:
    args = sys.argv[1:]
    if not args:
        target = "era-presentation"
    elif args[0] == "all":
        target = "all"
    else:
        target = args[0]

    if target == "all":
        for name in _SPECS:
            _upload(_SPECS[name])
            print()
        return

    if target not in _SPECS:
        sys.exit(f"Unknown skill {target!r}. Choose from: {', '.join(_SPECS)} | all")
    _upload(_SPECS[target])


if __name__ == "__main__":
    main()

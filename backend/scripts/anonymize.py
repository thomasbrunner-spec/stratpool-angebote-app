"""Apply per-offer redact mappings from bestandsangebote.yaml.

Usage:
    uv run python -m scripts.anonymize <slug>          # print anonymized text
    uv run python -m scripts.anonymize --check <slug>  # show which redact keys never matched

The redact map is applied in order of decreasing key length so that longer
spellings ("HumanTech Spine GmbH") win over shorter ones ("HumanTech").
String matching is case-sensitive; add explicit case variants to the map
if you need them.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.extract import extract


def anonymize(text: str, redact_map: dict[str, str]) -> str:
    for original in sorted(redact_map.keys(), key=len, reverse=True):
        text = text.replace(original, redact_map[original])
    return text


def find_unmatched_keys(text: str, redact_map: dict[str, str]) -> list[str]:
    return [k for k in redact_map if k not in text]


def load_offers(yaml_path: Path) -> list[dict[str, Any]]:
    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("offers", [])


def get_offer(offers: list[dict[str, Any]], slug: str) -> dict[str, Any]:
    for o in offers:
        if o.get("slug") == slug:
            return o
    raise KeyError(f"slug not found: {slug}")


def _yaml_path() -> Path:
    return Path(__file__).resolve().parent.parent / "seeds" / "bestandsangebote.yaml"


def main() -> None:
    args = sys.argv[1:]
    check_mode = False
    if args and args[0] == "--check":
        check_mode = True
        args = args[1:]
    if len(args) != 1:
        print(
            "Usage: python -m scripts.anonymize [--check] <slug>",
            file=sys.stderr,
        )
        sys.exit(2)
    slug = args[0]
    offers = load_offers(_yaml_path())
    offer = get_offer(offers, slug)
    raw = extract(Path(offer["source_file"]))
    redact_map: dict[str, str] = offer.get("redact") or {}
    if check_mode:
        unmatched = find_unmatched_keys(raw, redact_map)
        if unmatched:
            print(f"[{slug}] redact keys never found in source ({len(unmatched)}):")
            for k in unmatched:
                print(f"  - {k!r}")
        else:
            print(f"[{slug}] all {len(redact_map)} redact keys matched at least once.")
        return
    print(anonymize(raw, redact_map))


if __name__ == "__main__":
    main()

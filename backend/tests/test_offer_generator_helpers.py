"""Unit tests for the pure helpers in offer_generator (no IO).

The orchestrating `generate_offer()` function is exercised via integration —
these tests pin the rendering primitives that shape the prompt.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.schemas.offer import OfferGenerateRequest
from app.services.offer_generator import (
    _build_query_text,
    _build_user_message,
    _content_to_markdown,
    _render_few_shot,
    _unwrap_tool_input,
)


@dataclass
class _FakeOffer:
    id: uuid.UUID
    client_name: str
    consulting_type: str
    status: str


@dataclass
class _FakeVersion:
    content_json: dict[str, Any]


@dataclass
class _FakeRetrieved:
    offer: _FakeOffer
    latest_version: _FakeVersion
    score: float


def _request() -> OfferGenerateRequest:
    return OfferGenerateRequest(
        client_name="Acme GmbH",
        consulting_type="ki_strategie",
        industry="Maschinenbau",
        price_eur=Decimal("12500.00"),
        transcript="Discovery Call vom 02.05.2026 — " + ("blah " * 20),
        user_notes="Quick wins in 4 Wochen.",
    )


def test_build_query_text_includes_all_fields() -> None:
    text = _build_query_text(_request())
    assert "Acme GmbH" in text
    assert "Maschinenbau" in text
    assert "ki_strategie" in text
    assert "12500.00" in text
    assert "Quick wins" in text
    assert "Discovery-Transkript" in text


def test_build_query_text_handles_missing_optionals() -> None:
    req = OfferGenerateRequest(
        client_name="Beta AG",
        consulting_type="workshop",
        industry=None,
        price_eur=Decimal("3000"),
        transcript="t" * 60,
        user_notes=None,
    )
    text = _build_query_text(req)
    assert "Branche: unbekannt" in text
    assert "Anmerkungen" not in text


def test_render_few_shot_legacy_markdown() -> None:
    rv = _FakeRetrieved(
        offer=_FakeOffer(
            id=uuid.uuid4(),
            client_name="Kunde A",
            consulting_type="prozessberatung",
            status="won",
        ),
        latest_version=_FakeVersion(
            content_json={"format": "legacy_markdown", "markdown": "# Inhalt\n\nText"}
        ),
        score=0.83,
    )
    rendered = _render_few_shot(rv)  # type: ignore[arg-type]
    assert "Kunde A" in rendered
    assert "prozessberatung" in rendered
    assert "won" in rendered
    assert "sim=0.83" in rendered
    assert "# Inhalt" in rendered


def test_render_few_shot_structured_v2_content() -> None:
    rv = _FakeRetrieved(
        offer=_FakeOffer(
            id=uuid.uuid4(),
            client_name="Kunde B",
            consulting_type="ki_strategie",
            status="sent",
        ),
        latest_version=_FakeVersion(
            content_json={
                "angebot_titel": "KI-Strategie für B",
                "client_name": "Kunde B",
                "management_summary": "Big picture about B.",
                "hook_quote": "Der Schlüssel liegt nicht in der Technologie.",
                "ausgangssituation": "Situation X",
                "phasen": [
                    {"nummer": 1, "titel": "Vorbereitung", "beschreibung": "Stakeholder-Interviews", "ergebnis": "Workshop-Konzept"},
                    {"nummer": 2, "titel": "Workshop", "beschreibung": "Ein Tag", "ergebnis": "Priorisierung"},
                ],
                "investition": "10k EUR",
            }
        ),
        score=0.91,
    )
    rendered = _render_few_shot(rv)  # type: ignore[arg-type]
    assert "KI-Strategie für B" in rendered
    assert "Phase 1 — Vorbereitung" in rendered
    assert "Phase 2 — Workshop" in rendered
    assert "10k EUR" in rendered
    assert "Big picture about B." in rendered


def test_content_to_markdown_handles_missing_fields() -> None:
    md = _content_to_markdown({"angebot_titel": "Nur Titel"})
    assert "Nur Titel" in md
    assert "Phase " not in md


def test_build_user_message_without_few_shots_or_knowledge() -> None:
    msg = _build_user_message(_request(), retrieved=[], knowledge=[])
    assert "Referenz-Angebote" not in msg
    assert "Domänen-Wissen" not in msg
    assert "Acme GmbH" in msg
    assert "Discovery-Call-Transkript" in msg
    assert "submit_offer" in msg


def _flat_payload() -> dict[str, Any]:
    """Mock OfferContent v2 payload — only need the keys, not full content."""
    return {
        "angebot_titel": "T",
        "client_name": "C",
        "management_summary": "summary",
        "hook_quote": "quote",
        "warum_jetzt_argumente": ["a", "b"],
        "ausgangssituation": "A",
        "erkannte_anwendungsfaelle": ["x", "y", "z"],
        "zielsetzung_und_ergebnis": "Z",
        "phasen": [{"nummer": 1, "titel": "P1", "beschreibung": "x", "ergebnis": "y"}],
        "technische_basis": [{"titel": "T", "beschreibung": "B"}],
        "mehrwert_3_ebenen": [],
        "leistungsumfang_items": [],
        "investition": "I",
        "naechste_schritte": "N",
    }


def test_unwrap_tool_input_passes_flat_payload_through() -> None:
    payload = _flat_payload()
    assert _unwrap_tool_input(payload) is payload


def test_unwrap_tool_input_unwraps_offer_wrapper() -> None:
    inner = _flat_payload()
    assert _unwrap_tool_input({"offer": inner}) is inner


def test_unwrap_tool_input_unwraps_arbitrary_single_key_wrapper() -> None:
    inner = _flat_payload()
    assert _unwrap_tool_input({"data": inner}) is inner


def test_unwrap_tool_input_does_not_unwrap_when_inner_is_unrelated() -> None:
    weird = {"offer": {"foo": "bar"}}
    assert _unwrap_tool_input(weird) == weird


def test_unwrap_tool_input_passes_partial_flat_through() -> None:
    # Even with only some fields at the top level, treat it as flat — the
    # wrapper-detection heuristic must not strip a legitimately partial payload.
    partial = {"angebot_titel": "T", "client_name": "C"}
    assert _unwrap_tool_input(partial) is partial


def test_build_user_message_with_few_shots() -> None:
    rv = _FakeRetrieved(
        offer=_FakeOffer(
            id=uuid.uuid4(),
            client_name="Kunde A",
            consulting_type="prozessberatung",
            status="won",
        ),
        latest_version=_FakeVersion(
            content_json={"format": "legacy_markdown", "markdown": "# Beispiel"}
        ),
        score=0.7,
    )
    msg = _build_user_message(_request(), retrieved=[rv], knowledge=[])  # type: ignore[list-item]
    assert "Referenz-Angebote" in msg
    assert "# Beispiel" in msg
    assert msg.index("Referenz-Angebote") < msg.index("Neues Angebot")


def test_build_user_message_with_knowledge_block_first() -> None:
    """Knowledge block must come BEFORE few-shots and BEFORE inputs."""
    from app.services.knowledge import RetrievedKnowledge

    @dataclass
    class _FakeChunk:
        chapter: str | None
        title: str | None
        text: str
        ord: int

    chunk = RetrievedKnowledge(
        chunk=_FakeChunk(chapter="3", title="Discovery Call", text="Was ein guter Discovery Call ausmacht.", ord=0),  # type: ignore[arg-type]
        score=0.85,
    )
    msg = _build_user_message(_request(), retrieved=[], knowledge=[chunk])
    assert "Domänen-Wissen" in msg
    assert msg.index("Domänen-Wissen") < msg.index("Neues Angebot")

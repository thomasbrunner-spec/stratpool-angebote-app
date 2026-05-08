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


def test_render_few_shot_structured_content() -> None:
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
                "ausgangssituation": "Situation X",
                "leistungsumfang_intro": "Wir liefern Y",
                "bestandteile": [
                    {"titel": "Auftakt", "beschreibung": "Workshop"},
                    {"titel": "Analyse", "beschreibung": "Bewertung"},
                ],
                "leistungserbringung": "Remote",
                "investition": "10k EUR",
                "rahmenbedingungen": "14 Tage",
            }
        ),
        score=0.91,
    )
    rendered = _render_few_shot(rv)  # type: ignore[arg-type]
    assert "KI-Strategie für B" in rendered
    assert "Bestandteil 1 — Auftakt" in rendered
    assert "Bestandteil 2 — Analyse" in rendered
    assert "10k EUR" in rendered


def test_content_to_markdown_handles_missing_fields() -> None:
    md = _content_to_markdown({"angebot_titel": "Nur Titel"})
    assert "Nur Titel" in md
    assert "Bestandteil" not in md


def test_build_user_message_without_few_shots() -> None:
    msg = _build_user_message(_request(), retrieved=[])
    assert "Referenz-Angebote" not in msg
    assert "Acme GmbH" in msg
    assert "Discovery-Call-Transkript" in msg
    assert "submit_offer" in msg


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
    msg = _build_user_message(_request(), retrieved=[rv])  # type: ignore[list-item]
    assert "Referenz-Angebote" in msg
    assert "# Beispiel" in msg
    assert msg.index("Referenz-Angebote") < msg.index("Neues Angebot")

"""Schema-level tests for the offer pipeline (no DB, no LLM, no embeddings)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.offer import (
    OfferContent,
    OfferContentBestandteil,
    OfferGenerateRequest,
    OfferStatusUpdate,
)


def _valid_request_kwargs() -> dict:
    return {
        "client_name": "Acme GmbH",
        "consulting_type": "ki_strategie",
        "industry": "Maschinenbau",
        "price_eur": Decimal("12500.00"),
        "transcript": "Discovery Call vom 02.05.2026 — " + ("blah " * 20),
        "user_notes": "Kunde will Quick-Wins in den ersten 4 Wochen.",
    }


def test_request_accepts_valid_payload() -> None:
    req = OfferGenerateRequest(**_valid_request_kwargs())
    assert req.consulting_type == "ki_strategie"
    assert req.price_eur == Decimal("12500.00")


def test_request_rejects_unknown_consulting_type() -> None:
    bad = _valid_request_kwargs()
    bad["consulting_type"] = "bogus"
    with pytest.raises(ValidationError):
        OfferGenerateRequest(**bad)


def test_request_rejects_zero_price() -> None:
    bad = _valid_request_kwargs()
    bad["price_eur"] = Decimal("0")
    with pytest.raises(ValidationError):
        OfferGenerateRequest(**bad)


def test_request_rejects_short_transcript() -> None:
    bad = _valid_request_kwargs()
    bad["transcript"] = "too short"
    with pytest.raises(ValidationError):
        OfferGenerateRequest(**bad)


def _valid_content_kwargs() -> dict:
    return {
        "angebot_titel": "KI-Strategie für Acme",
        "client_name": "Acme GmbH",
        "ausgangssituation": "Acme will Use-Cases priorisieren.",
        "leistungsumfang_intro": "Wir liefern in drei Bestandteilen.",
        "bestandteile": [
            {"titel": "Kick-off", "beschreibung": "Auftakt-Workshop."},
            {"titel": "Analyse", "beschreibung": "Use-Case-Bewertung."},
        ],
        "leistungserbringung": "Remote, 4 Wochen.",
        "investition": "12.500 EUR Festpreis exkl. MwSt.",
        "rahmenbedingungen": "Zahlungsziel 14 Tage.",
    }


def test_content_round_trips_via_model_dump() -> None:
    content = OfferContent(**_valid_content_kwargs())
    dumped = content.model_dump(mode="json")
    rebuilt = OfferContent.model_validate(dumped)
    assert rebuilt == content
    assert isinstance(dumped["bestandteile"], list)
    assert dumped["bestandteile"][0]["titel"] == "Kick-off"


def test_content_rejects_empty_bestandteile() -> None:
    bad = _valid_content_kwargs()
    bad["bestandteile"] = []
    with pytest.raises(ValidationError):
        OfferContent(**bad)


def test_content_rejects_too_many_bestandteile() -> None:
    bad = _valid_content_kwargs()
    bad["bestandteile"] = [
        {"titel": f"B{i}", "beschreibung": "x"} for i in range(9)
    ]
    with pytest.raises(ValidationError):
        OfferContent(**bad)


def test_content_parses_bestandteile_when_claude_sends_json_string() -> None:
    """Claude Opus 4.7 sometimes returns the nested array as a JSON string."""
    import json

    kwargs = _valid_content_kwargs()
    kwargs["bestandteile"] = json.dumps(kwargs["bestandteile"])
    content = OfferContent(**kwargs)
    assert len(content.bestandteile) == 2
    assert content.bestandteile[0].titel == "Kick-off"


def test_content_rejects_unparseable_bestandteile_string() -> None:
    bad = _valid_content_kwargs()
    bad["bestandteile"] = "not even close to JSON"
    with pytest.raises(ValidationError):
        OfferContent(**bad)


def test_bestandteil_requires_titel_and_beschreibung() -> None:
    with pytest.raises(ValidationError):
        OfferContentBestandteil(titel="", beschreibung="ok")
    with pytest.raises(ValidationError):
        OfferContentBestandteil(titel="ok", beschreibung="")


def test_content_json_schema_has_anthropic_friendly_shape() -> None:
    """Anthropic tool input_schema requires properties + required at the root."""
    schema = OfferContent.model_json_schema()
    assert schema["type"] == "object"
    assert "bestandteile" in schema["properties"]
    assert set(schema["required"]) == {
        "angebot_titel",
        "client_name",
        "ausgangssituation",
        "leistungsumfang_intro",
        "bestandteile",
        "leistungserbringung",
        "investition",
        "rahmenbedingungen",
    }


def test_status_update_accepts_known_values() -> None:
    for s in ("draft", "sent", "won", "lost"):
        assert OfferStatusUpdate(status=s).status == s  # type: ignore[arg-type]


def test_status_update_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError):
        OfferStatusUpdate(status="archived")  # type: ignore[arg-type]

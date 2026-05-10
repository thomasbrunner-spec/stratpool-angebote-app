"""Schema-level tests for the v2 offer pipeline (no DB, no LLM, no embeddings)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.offer import (
    OfferContent,
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
        "management_summary": (
            "Acme GmbH steht an einem Wendepunkt: zwei Wissensträger im Einkauf "
            "scheiden in den nächsten Monaten aus, gleichzeitig steigen "
            "Routineanforderungen weiter an. Die hier vorgeschlagene "
            "KI-Strategie identifiziert mit dem Führungskreis 2–3 priorisierte "
            "Anwendungsfälle, bewertet sie wirtschaftlich und liefert eine "
            "umsetzungsfähige Roadmap. Am Ende stehen sichtbare Quick-Wins, "
            "ein klarer Fahrplan und ein gemeinsames Verständnis im Team."
        ),
        "hook_quote": (
            "Der Schlüssel liegt nicht in der Technologie, sondern in der "
            "Fähigkeit, relevante Anwendungsfälle zu identifizieren, zu "
            "priorisieren und schnell in erste Prototypen zu übersetzen."
        ),
        "warum_jetzt_argumente": [
            "KI-Nutzung im Mittelstand hat sich binnen eines Jahres verdoppelt.",
            "Wer wartet, verliert nicht linear, sondern exponentiell.",
            "Erste Anwendungsfälle bei Acme sind heute schon greifbar.",
        ],
        "ausgangssituation": (
            "Acme operiert in einem reifen Markt mit hohem Kostendruck. Im "
            "Einkauf scheiden zentrale Wissensträger aus, Routineprozesse "
            "binden viel Zeit. Eine vorhandene M365-Lizenz wird kaum genutzt; "
            "es existieren erste Punktlösungen ohne übergreifenden Rahmen."
        ),
        "erkannte_anwendungsfaelle": [
            "Automatisierter Abgleich von Wareneingangsdifferenzen",
            "KI-gestützte Lieferantenrecherche und Verhandlungsvorbereitung",
            "Wissenssicherung vor Ausscheiden zentraler Personen",
            "Chatbot auf Richtlinien und Betriebsvereinbarungen",
        ],
        "zielsetzung_und_ergebnis": (
            "Ziel ist eine priorisierte Liste von 2–3 Anwendungsfällen mit "
            "Business Case, technischer Bewertung und Roadmap. Daraus "
            "entstehen sichtbare Prototypen und eine Entscheidungsgrundlage "
            "für die Geschäftsführung."
        ),
        "phasen": [
            {
                "nummer": 1,
                "titel": "Vorbereitung",
                "untertitel": "Fundament für den Workshop",
                "beschreibung": (
                    "Wir führen kurze Stakeholder-Interviews und sichten die "
                    "vorhandene Tool-Landschaft, bevor wir in den Workshop "
                    "gehen. So gewinnen wir Tiefe ohne Aufwärmschleifen."
                ),
                "dauer": "ca. 2 Wochen",
                "format": "remote",
                "teilnehmer": "3–5 Schlüsselpersonen",
                "moderation": "Senior Partner ERA Group",
                "aktivitaeten": ["Interviews", "Online-Umfrage", "Sichtung Tool-Landschaft"],
                "ergebnis": "Workshop-Konzept und Stimmungsbild",
            },
            {
                "nummer": 2,
                "titel": "Strategischer Workshop",
                "beschreibung": (
                    "Ein voller Workshop-Tag mit dem Führungskreis. Wir "
                    "identifizieren und priorisieren Anwendungsfelder, "
                    "bewerten Aufwand und Nutzen und legen die Roadmap an."
                ),
                "dauer": "ein Tag",
                "format": "vor Ort",
                "teilnehmer": "6–8 Personen aus Führung",
                "moderation": "zwei Senior Partner",
                "aktivitaeten": ["Triggerkarten", "Bewertungsrunden", "Priorisierung"],
                "ergebnis": "Priorisierte Anwendungsfälle plus Roadmap-Skizze",
            },
        ],
        "technische_basis": [
            {
                "titel": "Lokal beim Kunden",
                "beschreibung": "Sensible Daten bleiben im Haus, einmaliger Investitionsaufwand, höchste Datenschutzsicherheit.",
            },
            {
                "titel": "Europäische Cloud",
                "beschreibung": "DSGVO-konforme EU-Rechenzentren, geringe Einstiegshürde, monatliche Nutzungsgebühren.",
            },
        ],
        "mehrwert_3_ebenen": [
            {
                "ebene": "Strategisch",
                "punkte": [
                    "Strukturierte KI-Roadmap mit Prioritäten",
                    "Entscheidungsgrundlage für die Geschäftsführung",
                    "Optionspfad zu einem KI-First-Geschäftsmodell",
                ],
            },
            {
                "ebene": "Organisatorisch",
                "punkte": [
                    "Transparente Bewertung von Prozessen und Potenzialen",
                    "Prototypen als sichtbarer Machbarkeitsnachweis",
                    "Klar bewertete Business Cases je Use Case",
                ],
            },
            {
                "ebene": "Menschlich",
                "punkte": [
                    "Beteiligung der Mitarbeitenden ohne technische Hürden",
                    "Stärkung von Akzeptanz und Lernbereitschaft",
                    "Entlastung des überlasteten Teams",
                ],
            },
        ],
        "leistungsumfang_items": [
            {"nummer": 1, "titel": "Vorbereitung & Konzeption", "beschreibung": "Feinabstimmung der Workshop-Ziele und Anpassung des Designs an Acme."},
            {"nummer": 2, "titel": "Stakeholder-Interviews", "beschreibung": "Gespräche mit Schlüsselpersonen zu Pain Points und Erwartungen."},
            {"nummer": 3, "titel": "Online-Umfrage", "beschreibung": "Erweiterung des Teilnehmerkreises über die Workshop-Gruppe hinaus."},
            {"nummer": 4, "titel": "Strategischer Workshop", "beschreibung": "Ganztägiger Workshop mit Moderation durch zwei Senior Partner."},
        ],
        "investition": (
            "Festpreis 12.500 EUR exkl. MwSt., inklusive aller im Leistungs"
            "umfang gelisteten Bestandteile. Reisekosten werden gesondert "
            "ausgewiesen. Zahlungsziel 14 Tage netto."
        ),
        "naechste_schritte": (
            "Wir schlagen einen 30-Minuten-Termin in der nächsten Woche vor, "
            "um den Vorschlag gemeinsam zu schärfen und die Stakeholder zu "
            "bestätigen."
        ),
    }


def test_content_round_trips_via_model_dump() -> None:
    content = OfferContent(**_valid_content_kwargs())
    dumped = content.model_dump(mode="json")
    rebuilt = OfferContent.model_validate(dumped)
    assert rebuilt == content
    assert isinstance(dumped["phasen"], list)
    assert dumped["phasen"][0]["titel"] == "Vorbereitung"


def test_content_rejects_too_few_phasen() -> None:
    bad = _valid_content_kwargs()
    bad["phasen"] = bad["phasen"][:1]
    with pytest.raises(ValidationError):
        OfferContent(**bad)


def test_content_requires_three_mehrwert_ebenen() -> None:
    bad = _valid_content_kwargs()
    bad["mehrwert_3_ebenen"] = bad["mehrwert_3_ebenen"][:2]
    with pytest.raises(ValidationError):
        OfferContent(**bad)


def test_content_parses_phasen_when_claude_sends_json_string() -> None:
    """Defensive validator: tolerate JSON-string-encoded nested arrays."""
    import json

    kwargs = _valid_content_kwargs()
    kwargs["phasen"] = json.dumps(kwargs["phasen"])
    content = OfferContent(**kwargs)
    assert len(content.phasen) == 2
    assert content.phasen[0].titel == "Vorbereitung"


def test_content_rejects_unparseable_string_for_list_field() -> None:
    bad = _valid_content_kwargs()
    bad["phasen"] = "not even close to JSON"
    with pytest.raises(ValidationError):
        OfferContent(**bad)


def test_content_json_schema_lists_all_v2_required_fields() -> None:
    """Anthropic tool input_schema requires properties + required at the root."""
    schema = OfferContent.model_json_schema()
    assert schema["type"] == "object"
    required = set(schema["required"])
    expected = {
        "angebot_titel",
        "client_name",
        "management_summary",
        "hook_quote",
        "warum_jetzt_argumente",
        "ausgangssituation",
        "erkannte_anwendungsfaelle",
        "zielsetzung_und_ergebnis",
        "phasen",
        "technische_basis",
        "mehrwert_3_ebenen",
        "leistungsumfang_items",
        "investition",
        "naechste_schritte",
    }
    assert required == expected


def test_status_update_accepts_known_values() -> None:
    for s in ("draft", "sent", "won", "lost"):
        assert OfferStatusUpdate(status=s).status == s  # type: ignore[arg-type]


def test_status_update_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError):
        OfferStatusUpdate(status="archived")  # type: ignore[arg-type]

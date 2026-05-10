"""Prompt-Viewer endpoint — read-only inspection of what we send to Claude.

Returns the static building blocks (system instructions, skeleton file)
plus an example user-message rendered with placeholder values, for both
the generate and render pipelines. No DB access; safe to call frequently.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.schemas.offer import OfferGenerateRequest
from app.services.auth import CurrentUser
from app.services import offer_generator, render_via_skill

settings = get_settings()
router = APIRouter(prefix="/prompts", tags=["prompts"])


class GeneratePromptInfo(BaseModel):
    model: str
    max_tokens: int
    system: str
    skeleton: str
    user_message_example: str
    user_message_notes: str


class RenderPromptInfo(BaseModel):
    model: str
    max_tokens: int
    betas: list[str]
    skills: dict[str, str]
    pptx_user_message_example: str
    word_user_message_example: str
    user_message_notes: str


class PromptsResponse(BaseModel):
    generate: GeneratePromptInfo
    render: RenderPromptInfo


def _example_generate_user_message() -> str:
    """Render the generate-pipeline user message with placeholders.

    Calls the real `_build_user_message` so future code changes
    automatically reflect in the viewer.
    """
    mock_request = OfferGenerateRequest(
        client_name="<KUNDE>",
        consulting_type="ki_strategie",
        industry="<BRANCHE>",
        price_eur=Decimal("1"),
        # >=50 chars to satisfy schema validation; rendered as a placeholder.
        transcript=("<DISCOVERY-CALL-TRANSKRIPT — voller Wortlaut des Termins>"),
        user_notes="<OPTIONAL: ANMERKUNGEN VOM BERATER>",
    )
    # No few-shots in the example; the prose blob below explains how they
    # would be inserted in a real call.
    return offer_generator._build_user_message(mock_request, retrieved=[])


def _example_render_user_message(fmt: render_via_skill.RenderFormat) -> str:
    """Render the render-pipeline user message text block with placeholders."""
    parts: list[dict[str, Any]] = render_via_skill._build_user_message(
        fmt=fmt,
        transcript="<DISCOVERY-CALL-TRANSKRIPT>",
        user_notes="<OPTIONAL: ANMERKUNGEN>",
        client_name="<KUNDE>",
        industry="<BRANCHE>",
        consulting_type="ki_strategie",
        price_eur=Decimal("1"),
        co_consultant=None,
        few_shot_file_ids=[],
    )
    text_blocks = [p["text"] for p in parts if p.get("type") == "text"]
    return "\n\n---\n\n".join(text_blocks)


@router.get("", response_model=PromptsResponse)
async def get_prompts(user: CurrentUser) -> PromptsResponse:
    """Return the prompts the generate and render pipelines actually use."""
    return PromptsResponse(
        generate=GeneratePromptInfo(
            model=settings.anthropic_model,
            max_tokens=offer_generator.MAX_OUTPUT_TOKENS,
            system=offer_generator.SYSTEM_INSTRUCTIONS,
            skeleton=offer_generator._load_skeleton(),
            user_message_example=_example_generate_user_message(),
            user_message_notes=(
                "Die User-Message wird pro Generierung aufgebaut. Vor den "
                "Eingabedaten stehen — sofern verfügbar — bis zu drei "
                "Referenz-Angebote als '## Referenz-Angebote (Stil und "
                "Struktur — nicht 1:1 kopieren)'-Block. Die werden über "
                "Voyage-Embeddings + pgvector aus dem Bestandsangebote-Pool "
                "ausgewählt."
            ),
        ),
        render=RenderPromptInfo(
            model=settings.render_model,
            max_tokens=16384,  # render_via_skill._MAX_TOKENS
            betas=list(render_via_skill._BETAS),
            skills={
                "pptx_builtin": "pptx",
                "word_builtin": "docx",
                "era_presentation_custom": settings.era_presentation_skill_id or "(nicht gesetzt)",
                "era_word_custom": settings.era_word_skill_id or "(nicht gesetzt)",
            },
            pptx_user_message_example=_example_render_user_message("pptx"),
            word_user_message_example=_example_render_user_message("word"),
            user_message_notes=(
                "Vor dem Text-Block können bis zu N container_upload-Blöcke "
                "stehen (Few-Shot-Decks aus FEW_SHOT_FILE_IDS). "
                "Aktuell konfiguriert: "
                f"{len(settings.few_shot_file_id_list)} Datei-IDs. Der "
                "Text-Block selbst hat ein cache_control=ephemeral, sodass "
                "Folge-Renderings innerhalb von ca. 5 Minuten den teuren "
                "Few-Shot-Anteil aus dem Anthropic-Cache ziehen."
            ),
        ),
    )

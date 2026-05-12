"""Pydantic schemas for the Hedy integration.

Mirrors the subset of the Hedy v1 REST API we expose to the frontend. We only
surface what the offer-generation flow actually needs:

  - Session list rows: id, title, startTime, duration — enough to pick.
  - Session detail: the cleaned transcript (fallback raw transcript) plus
    user-authored session notes. No recap, no highlights, no todos — those
    are Hedy's own AI artifacts and would bias our generator if injected.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HedySessionListItem(BaseModel):
    """One row in the Hedy session picker."""

    session_id: str = Field(serialization_alias="sessionId")
    title: str
    start_time: datetime = Field(serialization_alias="startTime")
    duration_minutes: int | None = Field(default=None, serialization_alias="durationMinutes")


class HedySessionList(BaseModel):
    """Paginated session list response."""

    items: list[HedySessionListItem]
    has_more: bool = Field(default=False, serialization_alias="hasMore")
    next_cursor: str | None = Field(default=None, serialization_alias="nextCursor")


class HedySessionDetail(BaseModel):
    """Detail payload we hand back to the frontend for pre-filling the form."""

    session_id: str = Field(serialization_alias="sessionId")
    title: str
    start_time: datetime = Field(serialization_alias="startTime")
    transcript: str = Field(description="cleaned_transcript with fallback to raw transcript")
    session_notes: str | None = Field(default=None, serialization_alias="sessionNotes")

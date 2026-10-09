"""Database tables. Characters and backgrounds are file-based (see assets.py)."""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlmodel import JSON, Column, Field, SQLModel


def _now() -> datetime:
    return datetime.now(UTC)


def _id() -> str:
    return uuid.uuid4().hex


class ProjectStatus(StrEnum):
    READY = "ready"  # text extracted, no script yet
    GENERATING = "generating"  # LLM is writing the script
    SCRIPTED = "scripted"  # script exists and can be edited
    FAILED = "failed"  # last script generation failed (see error)


class RenderStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELED = "canceled"


class ScriptStep(StrEnum):
    """Progress of script generation, shown on the "Writing script" screen."""

    IDEAS = "ideas"  # finding the key ideas
    JOKES = "jokes"  # writing the dialogue
    CHECK = "check"  # validating the lines


class CaptionStyle(StrEnum):
    BOLD_POP = "bold-pop"
    CLEAN = "clean"
    OUTLINE = "outline"


VIDEO_LENGTHS = (30, 60, 90)


class Project(SQLModel, table=True):
    id: str = Field(default_factory=_id, primary_key=True)
    title: str
    subject: str | None = None  # short course label from the LLM, e.g. "Biology"
    status: ProjectStatus = ProjectStatus.READY
    error: str | None = None
    # Source: an uploaded PDF or text file, or pasted notes ("source_kind" = pdf | text | notes).
    source_kind: str = "pdf"
    source_name: str | None = None
    pdf_path: str
    page_count: int
    pages: str | None = None  # page selection used for extraction, e.g. "1-5"
    extracted_text: str
    # Options chosen before writing the script
    length_s: int = 60
    taglish: bool = True
    # Script generation progress and results
    script_step: ScriptStep | None = None
    script_started_at: datetime | None = None
    key_ideas: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    # Style last chosen for this video (the next render uses it)
    background_id: str | None = None
    caption_style: CaptionStyle = CaptionStyle.BOLD_POP
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Line(SQLModel, table=True):
    id: str = Field(default_factory=_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    position: int
    character_id: str
    text: str
    # Cached preview/render audio; cleared whenever text or character changes.
    audio_path: str | None = None
    audio_key: str | None = None
    audio_duration_s: float | None = None


class Render(SQLModel, table=True):
    id: str = Field(default_factory=_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    status: RenderStatus = RenderStatus.QUEUED
    step: str | None = None
    progress: float = 0.0
    style_options: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    output_path: str | None = None
    duration_s: float | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

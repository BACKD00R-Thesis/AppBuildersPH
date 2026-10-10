"""Request and response bodies for the REST API (mounted under /api)."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import (
    VIDEO_LENGTHS,
    CaptionStyle,
    Line,
    Project,
    ProjectStatus,
    Render,
    RenderStatus,
    ScriptStep,
    VoiceStyle,
)

API_PREFIX = "/api"
SPEECH_WPS = 2.75  # matches tts.TARGET_WPS; used to estimate unvoiced line lengths


class LineOut(BaseModel):
    id: str
    position: int
    character_id: str
    text: str
    seconds: float  # spoken length: measured once voiced, estimated before that
    voiced: bool

    @classmethod
    def of(cls, line: Line) -> "LineOut":
        voiced = line.audio_duration_s is not None
        estimate = max(len(line.text.split()) / SPEECH_WPS, 1.0)
        return cls(
            id=line.id,
            position=line.position,
            character_id=line.character_id,
            text=line.text,
            seconds=round(line.audio_duration_s if voiced else estimate, 1),
            voiced=voiced,
        )


class RenderOut(BaseModel):
    id: str
    project_id: str
    status: RenderStatus
    step: str | None
    progress: float
    background_id: str | None
    caption_style: str | None
    duration_s: float | None
    error: str | None
    video_url: str | None
    created_at: datetime

    @classmethod
    def of(cls, render: Render) -> "RenderOut":
        options = render.style_options or {}
        return cls(
            id=render.id,
            project_id=render.project_id,
            status=render.status,
            step=render.step,
            progress=render.progress,
            background_id=options.get("background_id"),
            caption_style=options.get("caption_style"),
            duration_s=render.duration_s,
            error=render.error,
            video_url=f"{API_PREFIX}/renders/{render.id}/video"
            if render.status == RenderStatus.DONE
            else None,
            created_at=render.created_at,
        )


def latest_done(renders: list[Render]) -> Render | None:
    """Newest finished render (renders are passed newest first)."""
    return next((r for r in renders if r.status == RenderStatus.DONE), None)


class ProjectSummary(BaseModel):
    id: str
    title: str
    subject: str | None
    status: ProjectStatus
    script_step: ScriptStep | None
    page_count: int
    line_count: int
    length_s: int
    background_id: str | None
    created_at: datetime
    latest_render: RenderOut | None  # newest render of any status
    video: RenderOut | None  # newest finished render

    @classmethod
    def of(cls, project: Project, line_count: int, renders: list[Render]) -> "ProjectSummary":
        done = latest_done(renders)
        return cls(
            id=project.id,
            title=project.title,
            subject=project.subject,
            status=project.status,
            script_step=project.script_step,
            page_count=project.page_count,
            line_count=line_count,
            length_s=project.length_s,
            background_id=project.background_id,
            created_at=project.created_at,
            latest_render=RenderOut.of(renders[0]) if renders else None,
            video=RenderOut.of(done) if done else None,
        )


class ProjectOut(BaseModel):
    id: str
    title: str
    subject: str | None
    status: ProjectStatus
    error: str | None
    source_kind: str
    source_name: str | None
    page_count: int
    pages: str | None
    text_preview: str
    text_chars: int
    length_s: int
    taglish: bool
    script_step: ScriptStep | None
    script_started_at: datetime | None
    key_ideas: list[str]
    background_id: str | None
    caption_style: CaptionStyle
    voice_style: VoiceStyle
    lines: list[LineOut]
    renders: list[RenderOut]  # newest first
    video: RenderOut | None  # newest finished render
    created_at: datetime

    @classmethod
    def of(cls, project: Project, lines: list[Line], renders: list[Render]) -> "ProjectOut":
        done = latest_done(renders)
        return cls(
            id=project.id,
            title=project.title,
            subject=project.subject,
            status=project.status,
            error=project.error,
            source_kind=project.source_kind,
            source_name=project.source_name,
            page_count=project.page_count,
            pages=project.pages,
            text_preview=project.extracted_text[:400],
            text_chars=len(project.extracted_text),
            length_s=project.length_s,
            taglish=project.taglish,
            script_step=project.script_step,
            script_started_at=project.script_started_at,
            key_ideas=list(project.key_ideas or []),
            background_id=project.background_id,
            caption_style=project.caption_style,
            voice_style=project.voice_style,
            lines=[LineOut.of(line) for line in lines],
            renders=[RenderOut.of(r) for r in renders],
            video=RenderOut.of(done) if done else None,
            created_at=project.created_at,
        )


class LineIn(BaseModel):
    id: str | None = None  # keep the id of an existing line so its cached audio is reused
    character_id: str
    text: str = Field(min_length=1, max_length=400)


class ScriptIn(BaseModel):
    lines: list[LineIn] = Field(min_length=1, max_length=60)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    background_id: str | None = None
    caption_style: CaptionStyle | None = None
    voice_style: VoiceStyle | None = None
    taglish: bool | None = None
    length_s: int | None = None

    def check(self) -> str | None:
        if self.length_s is not None and self.length_s not in VIDEO_LENGTHS:
            return f"Video length must be one of {VIDEO_LENGTHS}"
        return None


class RenderIn(BaseModel):
    # Both default to the project's saved style.
    background_id: str | None = None
    caption_style: CaptionStyle | None = None


class AudioOut(BaseModel):
    audio_url: str
    duration_s: float

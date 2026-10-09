"""Request and response bodies for the REST API."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import Line, Project, ProjectStatus, Render, RenderStatus


class LineOut(BaseModel):
    id: str
    position: int
    character_id: str
    text: str

    @classmethod
    def of(cls, line: Line) -> "LineOut":
        return cls(id=line.id, position=line.position, character_id=line.character_id, text=line.text)


class RenderOut(BaseModel):
    id: str
    project_id: str
    status: RenderStatus
    step: str | None
    progress: float
    background_id: str | None
    duration_s: float | None
    error: str | None
    video_url: str | None
    created_at: datetime

    @classmethod
    def of(cls, render: Render) -> "RenderOut":
        return cls(
            id=render.id,
            project_id=render.project_id,
            status=render.status,
            step=render.step,
            progress=render.progress,
            background_id=(render.style_options or {}).get("background_id"),
            duration_s=render.duration_s,
            error=render.error,
            video_url=f"/renders/{render.id}/video" if render.status == RenderStatus.DONE else None,
            created_at=render.created_at,
        )


class ProjectSummary(BaseModel):
    id: str
    title: str
    status: ProjectStatus
    page_count: int
    created_at: datetime
    latest_render: RenderOut | None


class ProjectOut(BaseModel):
    id: str
    title: str
    status: ProjectStatus
    error: str | None
    page_count: int
    pages: str | None
    text_preview: str
    text_chars: int
    lines: list[LineOut]
    renders: list[RenderOut]
    created_at: datetime

    @classmethod
    def of(cls, project: Project, lines: list[Line], renders: list[Render]) -> "ProjectOut":
        return cls(
            id=project.id,
            title=project.title,
            status=project.status,
            error=project.error,
            page_count=project.page_count,
            pages=project.pages,
            text_preview=project.extracted_text[:400],
            text_chars=len(project.extracted_text),
            lines=[LineOut.of(line) for line in lines],
            renders=[RenderOut.of(r) for r in renders],
            created_at=project.created_at,
        )


class LineIn(BaseModel):
    id: str | None = None  # keep the id of an existing line so its cached audio is reused
    character_id: str
    text: str = Field(min_length=1, max_length=400)


class ScriptIn(BaseModel):
    lines: list[LineIn] = Field(min_length=1, max_length=60)


class ProjectUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class RenderIn(BaseModel):
    background_id: str | None = None


class PreviewOut(BaseModel):
    audio_url: str
    duration_s: float

import shutil
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlmodel import Session, select

from app import jobs, workflow
from app.assets import load_backgrounds, load_characters
from app.config import Settings, get_settings
from app.db import get_session
from app.deps import require_token
from app.models import VIDEO_LENGTHS, Line, Project, ProjectStatus, Render, VoiceStyle
from app.pipeline import tts
from app.pipeline.extract import ExtractError, decode_text_file, extract_pdf, extract_text
from app.schemas import ProjectOut, ProjectSummary, ProjectUpdate, ScriptIn

router = APIRouter(prefix="/projects", tags=["projects"], dependencies=[Depends(require_token)])

TEXT_SUFFIXES = {".txt", ".md", ".markdown"}


def get_project(project_id: str, session: Session) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Video not found")
    return project


def renders_for(session: Session, project_id: str) -> list[Render]:
    return list(
        session.exec(select(Render).where(Render.project_id == project_id).order_by(Render.created_at.desc()))
    )


def project_out(session: Session, project: Project) -> ProjectOut:
    return ProjectOut.of(
        project, workflow.ordered_lines(session, project.id), renders_for(session, project.id)
    )


def unprocessable(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, message)


@router.get("", response_model=list[ProjectSummary])
def list_projects(session: Session = Depends(get_session)) -> list[ProjectSummary]:
    projects = session.exec(select(Project).order_by(Project.created_at.desc())).all()
    counts = dict(session.exec(select(Line.project_id, func.count()).group_by(Line.project_id)).all())
    return [ProjectSummary.of(p, counts.get(p.id, 0), renders_for(session, p.id)) for p in projects]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    file: UploadFile | None = File(default=None, description="PDF, .txt or .md"),
    notes: str | None = Form(default=None, description="Pasted notes, instead of a file"),
    title: str | None = Form(default=None),
    pages: str | None = Form(default=None, description='PDF page selection, e.g. "1-5, 8"'),
    length_s: int = Form(default=60),
    taglish: bool = Form(default=False),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ProjectOut:
    """Create a video from a file or pasted notes. Then POST /projects/{id}/script to write it."""
    if length_s not in VIDEO_LENGTHS:
        raise unprocessable(f"Video length must be one of {VIDEO_LENGTHS}")
    pages = pages.strip() if pages and pages.strip() else None
    data: bytes | None = None
    try:
        if file is not None and file.filename:
            data = await file.read(settings.max_pdf_bytes + 1)
            if len(data) > settings.max_pdf_bytes:
                limit_mb = settings.max_pdf_bytes // (1024 * 1024)
                raise HTTPException(
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Files are limited to {limit_mb} MB"
                )
            suffix = Path(file.filename).suffix.lower()
            if suffix in TEXT_SUFFIXES or (file.content_type or "").startswith("text/"):
                kind, source_name = "text", file.filename
                extracted = extract_text(decode_text_file(data), settings.max_notes_chars)
            elif suffix == ".pdf" or data.startswith(b"%PDF"):
                kind, source_name = "pdf", file.filename
                extracted = extract_pdf(data, pages, settings.max_pdf_pages)
            else:
                raise unprocessable("Use a PDF, a .txt or .md file, or paste your notes")
        elif notes and notes.strip():
            kind, source_name = "notes", None
            extracted = extract_text(notes, settings.max_notes_chars)
        else:
            raise unprocessable("Choose a file or paste some notes")
    except ExtractError as exc:
        raise unprocessable(str(exc)) from exc

    project = Project(
        title=(title or "").strip()[:120] or workflow.default_title(source_name),
        source_kind=kind,
        source_name=source_name,
        pdf_path="",
        page_count=extracted.page_count,
        pages=pages if kind == "pdf" else None,
        extracted_text=extracted.text,
        length_s=length_s,
        taglish=taglish,
        background_id=next((b.id for b in load_backgrounds(settings)), None),
    )
    folder = workflow.project_dir(settings, project.id)
    folder.mkdir(parents=True, exist_ok=True)
    source_path = folder / ("source.pdf" if kind == "pdf" else "source.txt")
    if data is not None and kind == "pdf":
        source_path.write_bytes(data)
    else:
        source_path.write_text(extracted.text, encoding="utf-8")
    project.pdf_path = str(source_path)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project_out(session, project)


@router.get("/{project_id}", response_model=ProjectOut)
def read_project(project_id: str, session: Session = Depends(get_session)) -> ProjectOut:
    return project_out(session, get_project(project_id, session))


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    body: ProjectUpdate,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ProjectOut:
    """Rename, or save style and options (background, captions, voice style, Taglish, length)."""
    project = get_project(project_id, session)
    if problem := body.check():
        raise unprocessable(problem)
    if body.background_id is not None and body.background_id not in {
        b.id for b in load_backgrounds(settings)
    }:
        raise unprocessable(f"Unknown background '{body.background_id}'")
    if (
        body.voice_style == VoiceStyle.EXPRESSIVE
        and not (expressive := tts.expressive_status(settings))["ok"]
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Expressive voices aren't set up on this laptop: {expressive['detail']}",
        )
    for name, value in body.model_dump(exclude_none=True).items():
        setattr(project, name, value.strip() if isinstance(value, str) and name == "title" else value)
    project.updated_at = datetime.now(UTC)
    session.add(project)
    session.commit()
    return project_out(session, project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> None:
    project = get_project(project_id, session)
    for render in renders_for(session, project_id):
        jobs.cancel_render(render.id)
        session.delete(render)
    for line in workflow.ordered_lines(session, project_id):
        session.delete(line)
    session.delete(project)
    session.commit()
    shutil.rmtree(workflow.project_dir(settings, project_id), ignore_errors=True)


@router.post("/{project_id}/script", response_model=ProjectOut, status_code=status.HTTP_202_ACCEPTED)
def generate_script(project_id: str, session: Session = Depends(get_session)) -> ProjectOut:
    """Start writing (or rewriting) the dialogue. Poll GET /projects/{id} until status changes."""
    project = get_project(project_id, session)
    if project.status == ProjectStatus.GENERATING:
        raise HTTPException(status.HTTP_409_CONFLICT, "The script is already being written")
    project.status = ProjectStatus.GENERATING
    project.error = None
    project.script_step = None
    project.script_started_at = datetime.now(UTC)
    project.updated_at = datetime.now(UTC)
    session.add(project)
    session.commit()
    jobs.submit_script(project_id)
    return project_out(session, project)


@router.put("/{project_id}/script", response_model=ProjectOut)
def save_script(
    project_id: str,
    body: ScriptIn,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ProjectOut:
    """Replace the script with the edited lines, in order."""
    project = get_project(project_id, session)
    if project.status == ProjectStatus.GENERATING:
        raise HTTPException(status.HTTP_409_CONFLICT, "Wait for the script to finish")
    known = {c.id for c in load_characters(settings)}
    existing = {line.id: line for line in workflow.ordered_lines(session, project_id)}
    kept: set[str] = set()
    for position, item in enumerate(body.lines):
        if item.character_id not in known:
            raise unprocessable(f"Unknown character '{item.character_id}'")
        text = " ".join(item.text.split())
        if not text:
            raise unprocessable(f"Line {position + 1} is empty")
        line = existing.get(item.id) if item.id else None
        if line is None:
            line = Line(project_id=project_id, position=position, character_id=item.character_id, text=text)
        else:
            kept.add(line.id)
            if line.text != text or line.character_id != item.character_id:
                line.audio_duration_s = None  # audio is keyed on text + voice and refreshes on demand
            line.position = position
            line.character_id = item.character_id
            line.text = text
        session.add(line)
    for line_id, line in existing.items():
        if line_id not in kept:
            session.delete(line)
    project.status = ProjectStatus.SCRIPTED
    project.error = None
    project.updated_at = datetime.now(UTC)
    session.add(project)
    session.commit()
    return project_out(session, project)

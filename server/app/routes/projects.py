import shutil
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session, select

from app import jobs, workflow
from app.assets import load_characters
from app.config import Settings, get_settings
from app.db import get_session
from app.deps import require_token
from app.models import Line, Project, ProjectStatus, Render
from app.pipeline.extract import ExtractError, extract_pdf
from app.schemas import ProjectOut, ProjectSummary, ProjectUpdate, RenderOut, ScriptIn

router = APIRouter(prefix="/projects", tags=["projects"], dependencies=[Depends(require_token)])


def get_project(project_id: str, session: Session) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


def renders_for(session: Session, project_id: str) -> list[Render]:
    return list(
        session.exec(select(Render).where(Render.project_id == project_id).order_by(Render.created_at.desc()))
    )


def project_out(session: Session, project: Project) -> ProjectOut:
    return ProjectOut.of(
        project, workflow.ordered_lines(session, project.id), renders_for(session, project.id)
    )


@router.get("", response_model=list[ProjectSummary])
def list_projects(session: Session = Depends(get_session)) -> list[ProjectSummary]:
    projects = session.exec(select(Project).order_by(Project.created_at.desc())).all()
    result = []
    for project in projects:
        latest = session.exec(
            select(Render).where(Render.project_id == project.id).order_by(Render.created_at.desc())
        ).first()
        result.append(
            ProjectSummary(
                id=project.id,
                title=project.title,
                status=project.status,
                page_count=project.page_count,
                created_at=project.created_at,
                latest_render=RenderOut.of(latest) if latest else None,
            )
        )
    return result


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    pages: str | None = Form(default=None),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ProjectOut:
    data = await file.read(settings.max_pdf_bytes + 1)
    if len(data) > settings.max_pdf_bytes:
        limit_mb = settings.max_pdf_bytes // (1024 * 1024)
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"PDFs are limited to {limit_mb} MB")
    try:
        extracted = extract_pdf(data, pages, settings.max_pdf_pages)
    except ExtractError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    project = Project(
        title=(title or file.filename or "Untitled").strip()[:120],
        pdf_path="",
        page_count=extracted.page_count,
        pages=pages.strip() if pages and pages.strip() else None,
        extracted_text=extracted.text,
    )
    folder = workflow.project_dir(settings, project.id)
    folder.mkdir(parents=True, exist_ok=True)
    pdf_path = folder / "source.pdf"
    pdf_path.write_bytes(data)
    project.pdf_path = str(pdf_path)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project_out(session, project)


@router.get("/{project_id}", response_model=ProjectOut)
def read_project(project_id: str, session: Session = Depends(get_session)) -> ProjectOut:
    return project_out(session, get_project(project_id, session))


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str, body: ProjectUpdate, session: Session = Depends(get_session)
) -> ProjectOut:
    project = get_project(project_id, session)
    project.title = body.title.strip()
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
        raise HTTPException(status.HTTP_409_CONFLICT, "A script is already being generated")
    project.status = ProjectStatus.GENERATING
    project.error = None
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
        raise HTTPException(status.HTTP_409_CONFLICT, "Wait for the script to finish generating")
    known = {c.id for c in load_characters(settings)}
    existing = {line.id: line for line in workflow.ordered_lines(session, project_id)}
    kept: set[str] = set()
    for position, item in enumerate(body.lines):
        if item.character_id not in known:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, f"Unknown character '{item.character_id}'"
            )
        text = " ".join(item.text.split())
        if not text:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Line {position + 1} is empty")
        line = existing.get(item.id) if item.id else None
        if line is None:
            line = Line(project_id=project_id, position=position, character_id=item.character_id, text=text)
        else:
            kept.add(line.id)
            line.position = position
            line.character_id = item.character_id
            line.text = text  # cached audio is keyed on text + voice, so it refreshes on change
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

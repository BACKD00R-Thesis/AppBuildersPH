from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from app import jobs, workflow
from app.assets import load_backgrounds
from app.config import Settings, get_settings
from app.db import get_session
from app.deps import require_token
from app.models import ProjectStatus, Render, RenderStatus
from app.routes.projects import get_project
from app.schemas import RenderIn, RenderOut

router = APIRouter(tags=["renders"], dependencies=[Depends(require_token)])

ACTIVE = (RenderStatus.QUEUED, RenderStatus.RUNNING)


def get_render(render_id: str, session: Session) -> Render:
    render = session.get(Render, render_id)
    if render is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Render not found")
    return render


@router.post("/projects/{project_id}/renders", response_model=RenderOut, status_code=status.HTTP_202_ACCEPTED)
def start_render(
    project_id: str,
    body: RenderIn,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RenderOut:
    project = get_project(project_id, session)
    if project.status == ProjectStatus.GENERATING:
        raise HTTPException(status.HTTP_409_CONFLICT, "Wait for the script to finish generating")
    if not workflow.ordered_lines(session, project_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "The script is empty")
    if body.background_id and body.background_id not in {b.id for b in load_backgrounds(settings)}:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"Unknown background '{body.background_id}'"
        )
    render = Render(project_id=project_id, style_options={"background_id": body.background_id})
    session.add(render)
    session.commit()
    session.refresh(render)
    jobs.submit_render(render.id)
    return RenderOut.of(render)


@router.get("/renders/{render_id}", response_model=RenderOut)
def read_render(render_id: str, session: Session = Depends(get_session)) -> RenderOut:
    return RenderOut.of(get_render(render_id, session))


@router.delete("/renders/{render_id}", response_model=RenderOut)
def cancel_render(render_id: str, session: Session = Depends(get_session)) -> RenderOut:
    """Cancel a queued or running render. Finished renders are left as they are."""
    render = get_render(render_id, session)
    if render.status in ACTIVE:
        jobs.cancel_render(render_id)
        if render.status == RenderStatus.QUEUED:
            render.status = RenderStatus.CANCELED
            render.updated_at = datetime.now(UTC)
            session.add(render)
            session.commit()
    return RenderOut.of(render)


@router.get("/renders/{render_id}/video")
def video(render_id: str, session: Session = Depends(get_session)) -> FileResponse:
    render = get_render(render_id, session)
    if render.status != RenderStatus.DONE or not render.output_path or not Path(render.output_path).exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Video isn't ready")
    project = get_project(render.project_id, session)
    safe_title = (
        "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in project.title).strip() or "video"
    )
    return FileResponse(render.output_path, media_type="video/mp4", filename=f"{safe_title}.mp4")

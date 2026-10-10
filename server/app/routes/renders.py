import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from app import jobs, workflow
from app.assets import load_backgrounds
from app.config import Settings, get_settings
from app.db import get_session
from app.deps import require_token
from app.models import ProjectStatus, Render, RenderStatus, VoiceStyle
from app.pipeline import tts
from app.routes.projects import get_project
from app.schemas import RenderIn, RenderOut

router = APIRouter(tags=["renders"], dependencies=[Depends(require_token)])

ACTIVE = (RenderStatus.QUEUED, RenderStatus.RUNNING)


def get_render(render_id: str, session: Session) -> Render:
    render = session.get(Render, render_id)
    if render is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Render not found")
    return render


def finished_video(render: Render) -> Path:
    if render.status != RenderStatus.DONE or not render.output_path or not Path(render.output_path).exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Video isn't ready")
    return Path(render.output_path)


@router.post("/projects/{project_id}/renders", response_model=RenderOut, status_code=status.HTTP_202_ACCEPTED)
def start_render(
    project_id: str,
    body: RenderIn,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RenderOut:
    """Render with the given style, or the project's saved style. The choice is saved on the project."""
    project = get_project(project_id, session)
    if project.status == ProjectStatus.GENERATING:
        raise HTTPException(status.HTTP_409_CONFLICT, "Wait for the script to finish")
    if not workflow.ordered_lines(session, project_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "The script is empty")
    background_id = body.background_id or project.background_id
    if background_id and background_id not in {b.id for b in load_backgrounds(settings)}:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Unknown background '{background_id}'")
    caption_style = body.caption_style or project.caption_style
    if (
        project.voice_style == VoiceStyle.EXPRESSIVE
        and not (expressive := tts.expressive_status(settings))["ok"]
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Expressive voices aren't set up on this laptop: {expressive['detail']}",
        )
    # The app follows the newest render, so an older one still queued or running would only
    # hold it at 0%. The newest choice of style wins.
    for active in session.exec(
        select(Render).where(
            Render.project_id == project_id,
            Render.status.in_([RenderStatus.QUEUED, RenderStatus.RUNNING]),
        )
    ):
        jobs.cancel_render(active.id)
    project.background_id = background_id
    project.caption_style = caption_style
    session.add(project)
    render = Render(
        project_id=project_id,
        style_options={
            "background_id": background_id,
            "caption_style": str(caption_style),
            "voice_style": str(project.voice_style),
        },
    )
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
def video(render_id: str, download: bool = False, session: Session = Depends(get_session)) -> FileResponse:
    """The MP4. `?download=1` asks the browser to save it instead of playing it."""
    render = get_render(render_id, session)
    path = finished_video(render)
    project = get_project(render.project_id, session)
    safe_title = (
        "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in project.title).strip() or "video"
    )
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"{safe_title}.mp4",
        content_disposition_type="attachment" if download else "inline",
    )


@router.post("/renders/{render_id}/reveal", status_code=status.HTTP_204_NO_CONTENT)
def reveal(render_id: str, session: Session = Depends(get_session)) -> None:
    """Show the MP4 in the file manager of the computer running the server ("Open folder")."""
    path = finished_video(get_render(render_id, session))
    if sys.platform == "win32":
        command = ["explorer", f"/select,{path}"]
    elif sys.platform == "darwin":
        command = ["open", "-R", str(path)]
    else:
        command = ["xdg-open", str(path.parent)]
    try:
        subprocess.Popen(command)  # noqa: S603  (fixed command, path from our own data dir)
    except OSError as exc:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Couldn't open a file manager here") from exc

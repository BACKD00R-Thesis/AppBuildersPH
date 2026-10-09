"""In-process background jobs.

One worker thread runs script generation and renders in order, so the LLM, TTS
and FFmpeg never compete for the same RAM. Fine for a single local user.
"""

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor

from sqlmodel import Session, select

from app import workflow
from app.config import get_settings
from app.db import get_engine
from app.models import Project, ProjectStatus, Render, RenderStatus

log = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="job")
_cancel_events: dict[str, threading.Event] = {}


def _log_failure(future: Future) -> None:
    if (exc := future.exception()) is not None:
        log.error("Background job crashed", exc_info=exc)


def submit_script(project_id: str) -> None:
    def run() -> None:
        with Session(get_engine()) as session:
            workflow.generate_script(session, project_id, get_settings())

    _executor.submit(run).add_done_callback(_log_failure)


def submit_render(render_id: str) -> None:
    cancel = threading.Event()
    _cancel_events[render_id] = cancel

    def run() -> None:
        try:
            with Session(get_engine()) as session:
                workflow.run_render(session, render_id, get_settings(), cancel)
        finally:
            _cancel_events.pop(render_id, None)

    _executor.submit(run).add_done_callback(_log_failure)


def cancel_render(render_id: str) -> bool:
    """Signal a queued or running render to stop. Returns False if it isn't active."""
    event = _cancel_events.get(render_id)
    if event is None:
        return False
    event.set()
    return True


def recover_interrupted() -> None:
    """Mark work that was in flight when the server stopped as failed."""
    with Session(get_engine()) as session:
        for job in session.exec(
            select(Render).where(Render.status.in_([RenderStatus.QUEUED, RenderStatus.RUNNING]))
        ):
            job.status = RenderStatus.FAILED
            job.error = "The server restarted during this render. Start it again."
            session.add(job)
        for project in session.exec(select(Project).where(Project.status == ProjectStatus.GENERATING)):
            project.status = ProjectStatus.FAILED
            project.error = "The server restarted while writing the script. Try again."
            session.add(project)
        session.commit()

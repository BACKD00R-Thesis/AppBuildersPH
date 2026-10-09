from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from app import workflow
from app.config import Settings, get_settings
from app.db import get_session
from app.deps import require_token
from app.models import Line
from app.pipeline.tts import TTSError, wav_duration
from app.schemas import PreviewOut

router = APIRouter(prefix="/lines", tags=["lines"], dependencies=[Depends(require_token)])


def get_line(line_id: str, session: Session) -> Line:
    line = session.get(Line, line_id)
    if line is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Line not found. Save the script first.")
    return line


@router.post("/{line_id}/preview", response_model=PreviewOut)
def preview(
    line_id: str,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> PreviewOut:
    """Synthesize one saved line (or reuse its cached audio) and return a URL to play it."""
    line = get_line(line_id, session)
    character = workflow.characters_by_id(settings).get(line.character_id)
    if character is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Unknown character '{line.character_id}'")
    try:
        path = workflow.ensure_line_audio(session, line, character, settings)
    except TTSError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    # The key in the URL busts any player cache when the text changes.
    return PreviewOut(audio_url=f"/lines/{line.id}/audio?v={line.audio_key}", duration_s=wav_duration(path))


@router.get("/{line_id}/audio")
def audio(line_id: str, session: Session = Depends(get_session)) -> FileResponse:
    line = get_line(line_id, session)
    if not line.audio_path or not Path(line.audio_path).exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No audio yet. Request a preview first.")
    return FileResponse(line.audio_path, media_type="audio/wav")

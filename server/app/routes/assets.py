from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.assets import Character, load_backgrounds, load_characters
from app.config import Settings, get_settings
from app.deps import require_token
from app.pipeline import tts

router = APIRouter(prefix="/assets", tags=["assets"], dependencies=[Depends(require_token)])


def get_character(character_id: str, settings: Settings) -> Character:
    character = next((c for c in load_characters(settings) if c.id == character_id), None)
    if character is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown character")
    return character


@router.get("/characters")
def characters(settings: Settings = Depends(get_settings)) -> list[dict]:
    return [c.public() for c in load_characters(settings)]


@router.get("/characters/{character_id}/image")
def character_image(character_id: str, settings: Settings = Depends(get_settings)) -> FileResponse:
    character = get_character(character_id, settings)
    if character.image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No image for this character")
    return FileResponse(character.image, media_type="image/png")


@router.get("/characters/{character_id}/sample")
def character_sample(character_id: str, settings: Settings = Depends(get_settings)) -> FileResponse:
    """A short line in this character's voice ("Hear sample"). Synthesized once, then cached."""
    character = get_character(character_id, settings)
    path = (
        settings.data_dir
        / "samples"
        / f"{character.id}-{tts.audio_key(character.sample, character, settings)}.wav"
    )
    if not path.exists():
        try:
            tts.synthesize(character.sample, character, path, settings)
        except tts.TTSError as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return FileResponse(path, media_type="audio/wav")


@router.get("/backgrounds")
def backgrounds(settings: Settings = Depends(get_settings)) -> list[dict]:
    return [b.public() for b in load_backgrounds(settings)]

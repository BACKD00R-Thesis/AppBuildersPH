from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.assets import load_backgrounds, load_characters
from app.config import Settings, get_settings
from app.deps import require_token

router = APIRouter(prefix="/assets", tags=["assets"], dependencies=[Depends(require_token)])


@router.get("/characters")
def characters(settings: Settings = Depends(get_settings)) -> list[dict]:
    return [c.public() for c in load_characters(settings)]


@router.get("/characters/{character_id}/image")
def character_image(character_id: str, settings: Settings = Depends(get_settings)) -> FileResponse:
    character = next((c for c in load_characters(settings) if c.id == character_id), None)
    if character is None or character.image is None:
        raise HTTPException(404, "No image for this character")
    return FileResponse(character.image, media_type="image/png")


@router.get("/backgrounds")
def backgrounds(settings: Settings = Depends(get_settings)) -> list[dict]:
    return [b.public() for b in load_backgrounds(settings)]

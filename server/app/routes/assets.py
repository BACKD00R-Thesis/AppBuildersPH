import json
import re
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.assets import Background, Character, load_backgrounds, load_characters
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


@router.get("/backgrounds/{background_id}/video")
def background_video(background_id: str, settings: Settings = Depends(get_settings)) -> FileResponse:
    background = next((b for b in load_backgrounds(settings) if b.id == background_id), None)
    if background is None or background.file is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No video for this background")
    media_types = {
        ".mp4": "video/mp4",
        ".m4v": "video/mp4",
        ".mov": "video/quicktime",
        ".webm": "video/webm",
    }
    return FileResponse(background.file, media_type=media_types.get(background.file.suffix.lower(), "video/mp4"))


def _background_manifest(settings: Settings) -> Path:
    return settings.assets_dir / "backgrounds" / "manifest.json"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "background"


def _unique(existing: set[str], value: str) -> str:
    candidate = value
    index = 2
    while candidate in existing:
        candidate = f"{value}-{index}"
        index += 1
    return candidate


@router.post("/backgrounds", status_code=status.HTTP_201_CREATED)
def upload_background(file: UploadFile = File(...), settings: Settings = Depends(get_settings)) -> dict:
    """Add a local video file as a selectable render background."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".mp4", ".mov", ".m4v", ".webm"}:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload an MP4, MOV, M4V, or WebM video.")

    base = settings.assets_dir / "backgrounds"
    base.mkdir(parents=True, exist_ok=True)
    manifest_path = _background_manifest(settings)
    entries = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []

    label = Path(file.filename or "Custom background").stem.strip() or "Custom background"
    background_id = _unique({str(entry.get("id", "")) for entry in entries}, f"custom-{_slug(label)}")
    filename = _unique({str(entry.get("file", "")) for entry in entries}, f"{background_id}{suffix}")
    destination = base / filename

    with destination.open("wb") as output:
        shutil.copyfileobj(file.file, output)

    entry = {
        "id": background_id,
        "name": label,
        "short_name": label,
        "gradient": ["#3b4a2e", "#151a14"],
        "file": filename,
        "duration_s": 300,
        "custom": True,
    }
    entries.append(entry)
    manifest_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")

    clip = destination if destination.exists() else None
    return Background(
        id=entry["id"],
        name=entry["name"],
        short_name=entry["short_name"],
        gradient=(entry["gradient"][0], entry["gradient"][1]),
        file=clip,
        duration_s=entry["duration_s"],
        custom=True,
    ).public()

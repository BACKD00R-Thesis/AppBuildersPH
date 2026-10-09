from fastapi import APIRouter, Depends, Header

from app.config import Settings, get_settings
from app.deps import token_matches
from app.pipeline import align, render, script, tts

router = APIRouter(tags=["health"])


@router.get("/health")
def health(
    x_pairing_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Liveness and engine status. Open without a token so the app can test the connection."""
    engines = {
        "llm": script.ollama_status(settings),
        "tts": tts.engine_status(settings),
        "alignment": (
            {"ok": True, "detail": f"faster-whisper ({settings.whisper_model})"}
            if align.whisper_available()
            else {"ok": True, "detail": "faster-whisper not installed; using estimated timing"}
        ),
        "ffmpeg": render.ffmpeg_status(settings),
    }
    return {
        "ok": True,
        "auth_required": bool(settings.api_pairing_token),
        "auth_ok": token_matches(x_pairing_token, settings),
        "engines": engines,
        "ready": all(e["ok"] for e in engines.values()),
    }

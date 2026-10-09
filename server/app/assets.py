"""Characters and backgrounds, loaded from assets/*/manifest.json.

Every background has a gradient (the same one the app previews). If its gameplay
clip is present in assets/backgrounds, renders use the clip; otherwise they use
the gradient, so a fresh checkout can render without any footage.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.config import Settings


@dataclass(frozen=True)
class Character:
    id: str
    name: str
    role: str  # "asker" (character A) or "explainer" (character B)
    persona: str
    color: str  # speaker label color in the video, hex "#RRGGBB"
    vibe: str = ""  # short description shown in the app, e.g. "Loud and slow"
    sample: str = "Hello! Let's study this together."  # line used for "Hear sample"
    voices: dict[str, str] = field(default_factory=dict)  # engine -> voice id / model file
    image: str | None = None  # path to a transparent PNG, if any

    def public(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "vibe": self.vibe,
            "color": self.color,
            "has_image": self.image is not None,
        }


@dataclass(frozen=True)
class Background:
    id: str
    name: str
    short_name: str
    gradient: tuple[str, str]  # top and bottom colors, "#RRGGBB"
    file: Path | None = None  # gameplay clip, if present
    duration_s: float | None = None

    def public(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "from": self.gradient[0],
            "to": self.gradient[1],
            "has_clip": self.file is not None,
        }


def _read_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def load_characters(settings: Settings) -> list[Character]:
    base = settings.assets_dir / "characters"
    characters = []
    for entry in _read_manifest(base / "manifest.json"):
        image = entry.get("image")
        image_path = base / image if image and (base / image).exists() else None
        characters.append(
            Character(
                id=entry["id"],
                name=entry["name"],
                role=entry["role"],
                persona=entry["persona"],
                color=entry.get("color", "#FFFFFF"),
                vibe=entry.get("vibe", ""),
                sample=entry.get("sample", Character.sample),
                voices=dict(entry.get("voices", {})),
                image=str(image_path) if image_path else None,
            )
        )
    _apply_voice_overrides(characters, settings)
    return characters


def _apply_voice_overrides(characters: list[Character], settings: Settings) -> None:
    """KOKORO_VOICE_A/B and PIPER_VOICE_A/B override the asker (A) and explainer (B) voices."""
    overrides = {
        "asker": {"kokoro": settings.kokoro_voice_a, "piper": settings.piper_voice_a},
        "explainer": {"kokoro": settings.kokoro_voice_b, "piper": settings.piper_voice_b},
    }
    for character in characters:
        for engine, voice in overrides.get(character.role, {}).items():
            if voice:
                character.voices[engine] = voice


def get_pair(characters: list[Character]) -> tuple[Character, Character]:
    """The (asker, explainer) pair used for scripts."""
    asker = next((c for c in characters if c.role == "asker"), None)
    explainer = next((c for c in characters if c.role == "explainer"), None)
    if asker is None or explainer is None:
        raise RuntimeError("assets/characters/manifest.json needs one 'asker' and one 'explainer'")
    return asker, explainer


def load_backgrounds(settings: Settings) -> list[Background]:
    base = settings.assets_dir / "backgrounds"
    backgrounds = []
    for entry in _read_manifest(base / "manifest.json"):
        clip = base / entry["file"] if entry.get("file") else None
        colors = entry.get("gradient") or ["#24242E", "#0E0E12"]
        backgrounds.append(
            Background(
                id=entry["id"],
                name=entry["name"],
                short_name=entry.get("short_name", entry["name"]),
                gradient=(colors[0], colors[1]),
                file=clip if clip and clip.exists() else None,
                duration_s=entry.get("duration_s"),
            )
        )
    return backgrounds

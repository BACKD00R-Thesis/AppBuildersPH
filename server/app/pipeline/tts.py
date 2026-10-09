"""Text-to-speech adapter: Kokoro (default), Piper (lighter), or dummy (no models needed).

Every engine writes a mono 16-bit WAV. Models load once and are reused.
"""

import hashlib
import importlib.util
import math
import threading
import wave
from array import array
from pathlib import Path

from app.assets import Character
from app.config import Settings

ENGINES = ("kokoro", "piper", "dummy")
DEFAULT_KOKORO_VOICE = "am_michael"


class TTSError(RuntimeError):
    pass


_lock = threading.Lock()
_kokoro_pipelines: dict[str, object] = {}
_piper_voices: dict[str, object] = {}


def voice_for(character: Character, settings: Settings) -> str:
    engine = settings.tts_engine
    if engine == "dummy":
        return character.role
    voice = character.voices.get(engine)
    if engine == "kokoro":
        return voice or DEFAULT_KOKORO_VOICE
    if not voice:
        raise TTSError(f"No Piper voice set for {character.name} (see PIPER_VOICE_A/B)")
    return voice


def audio_key(text: str, character: Character, settings: Settings) -> str:
    """Identifies a synthesized clip, so unchanged lines reuse cached audio."""
    raw = f"{settings.tts_engine}|{voice_for(character, settings)}|{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / float(wav.getframerate())


def synthesize(text: str, character: Character, out_path: Path, settings: Settings) -> float:
    """Synthesize `text` to `out_path` and return the duration in seconds."""
    if settings.tts_engine not in ENGINES:
        raise TTSError(f"Unknown TTS_ENGINE '{settings.tts_engine}' (use one of {ENGINES})")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    voice = voice_for(character, settings)
    with _lock:
        if settings.tts_engine == "kokoro":
            _kokoro(text, voice, out_path)
        elif settings.tts_engine == "piper":
            _piper(text, voice, out_path, settings)
        else:
            _dummy(text, character, out_path)
    return wav_duration(out_path)


def _kokoro(text: str, voice: str, out_path: Path) -> None:
    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
    except ImportError as exc:
        raise TTSError(
            "Kokoro isn't installed. Run: pip install -r requirements-engines.txt (or set TTS_ENGINE=dummy)"
        ) from exc
    # Voice ids start with the language: a = American English, b = British English.
    lang = voice[0] if voice[:1] in ("a", "b") else "a"
    pipeline = _kokoro_pipelines.get(lang)
    if pipeline is None:
        pipeline = KPipeline(lang_code=lang)
        _kokoro_pipelines[lang] = pipeline
    chunks = []
    for _, _, audio in pipeline(text, voice=voice, speed=1.05):
        if audio is not None:
            chunks.append(audio.numpy() if hasattr(audio, "numpy") else np.asarray(audio))
    if not chunks:
        raise TTSError(f"Kokoro produced no audio for: {text[:60]}")
    sf.write(str(out_path), np.concatenate(chunks), 24000, subtype="PCM_16")


def _piper(text: str, voice: str, out_path: Path, settings: Settings) -> None:
    try:
        from piper import PiperVoice
    except ImportError as exc:
        raise TTSError("Piper isn't installed. Run: pip install -r requirements-engines.txt") from exc
    model_path = Path(voice)
    if not model_path.is_absolute():
        model_path = settings.models_dir / model_path
    if not model_path.exists():
        raise TTSError(f"Piper voice model not found: {model_path}")
    piper_voice = _piper_voices.get(str(model_path))
    if piper_voice is None:
        piper_voice = PiperVoice.load(str(model_path))
        _piper_voices[str(model_path)] = piper_voice
    with wave.open(str(out_path), "wb") as wav:
        if hasattr(piper_voice, "synthesize_wav"):  # piper-tts >= 1.3
            piper_voice.synthesize_wav(text, wav)
        else:
            piper_voice.synthesize(text, wav)


def _dummy(text: str, character: Character, out_path: Path) -> None:
    """A soft blip per word at a speech-like pace. For development without TTS models."""
    rate = 24000
    words = text.split() or ["…"]
    per_word = 0.3
    pitch = 520.0 if character.role == "asker" else 330.0
    samples = array("h", [0] * int(rate * (len(words) * per_word + 0.2)))
    blip = int(rate * 0.08)
    for i in range(len(words)):
        start = int(rate * i * per_word)
        for n in range(blip):
            envelope = math.sin(math.pi * n / blip)
            samples[start + n] = int(6000 * envelope * math.sin(2 * math.pi * pitch * n / rate))
    with wave.open(str(out_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(samples.tobytes())


def engine_status(settings: Settings) -> dict:
    engine = settings.tts_engine
    if engine == "dummy":
        return {"ok": True, "detail": "dummy (placeholder blips, no real voices)"}
    module = {"kokoro": "kokoro", "piper": "piper"}.get(engine)
    if module is None:
        return {"ok": False, "detail": f"Unknown TTS_ENGINE '{engine}'"}
    if importlib.util.find_spec(module) is None:
        return {"ok": False, "detail": f"{engine} not installed (pip install -r requirements-engines.txt)"}
    return {"ok": True, "detail": engine}

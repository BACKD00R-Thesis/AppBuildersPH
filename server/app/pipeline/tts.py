"""Text-to-speech adapter: Kokoro (default), Piper (lighter), or dummy (no models needed).

Every engine writes a mono 16-bit WAV. Models load once and are reused. Speech is
kept at 2.5-3 words per second so the captions it drives stay readable: clips
outside that range are time-stretched (pitch preserved) with FFmpeg.
"""

import hashlib
import importlib.util
import logging
import math
import subprocess
import threading
import wave
from array import array
from pathlib import Path

from app.assets import Character
from app.config import Settings

log = logging.getLogger(__name__)

ENGINES = ("kokoro", "piper", "dummy")
DEFAULT_KOKORO_VOICE = "am_michael"

# Readable caption pace (words per second). Changing these re-synthesizes cached clips.
MIN_WPS, MAX_WPS, TARGET_WPS = 2.5, 3.0, 2.75
# Very short lines ("Wait, what?") are mostly silence padding; their rate isn't meaningful.
MIN_WORDS_TO_PACE = 4
PACE_VERSION = f"pace-{MIN_WPS}-{MAX_WPS}"


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
    raw = f"{settings.tts_engine}|{voice_for(character, settings)}|{PACE_VERSION}|{text}"
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
    pace_clip(out_path, len(text.split()), settings)
    return wav_duration(out_path)


def speech_rate(path: Path, word_count: int) -> float:
    return word_count / max(wav_duration(path), 0.01)


def pace_clip(path: Path, word_count: int, settings: Settings) -> None:
    """Time-stretch a clip into MIN_WPS..MAX_WPS words per second, keeping its pitch."""
    if word_count < MIN_WORDS_TO_PACE:
        return
    rate = speech_rate(path, word_count)
    if MIN_WPS <= rate <= MAX_WPS:
        return
    # atempo > 1 speeds up; playing at TARGET_WPS/rate turns `rate` into TARGET_WPS.
    tempo = min(max(TARGET_WPS / rate, 0.5), 2.0)
    tmp = path.with_suffix(".paced.wav")
    try:
        subprocess.run(
            [
                settings.ffmpeg_path, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(path), "-filter:a", f"atempo={tempo:.4f}", "-c:a", "pcm_s16le", str(tmp),
            ],
            check=True,
            capture_output=True,
        )  # fmt: skip
        tmp.replace(path)
    except (OSError, subprocess.CalledProcessError) as exc:
        # Pacing is a readability improvement, not a requirement: keep the original clip.
        log.warning("Couldn't adjust speech pace for %s: %s", path, exc)
        tmp.unlink(missing_ok=True)


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
    for _, _, audio in pipeline(text, voice=voice, speed=1.0):
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


def _dummy(text: str, character: Character, out_path: Path, words_per_second: float = TARGET_WPS) -> None:
    """A soft blip per word at a readable pace. For development without TTS models."""
    rate = 24000
    words = text.split() or ["…"]
    per_word = 1.0 / words_per_second
    pitch = 520.0 if character.role == "asker" else 330.0
    samples = array("h", [0] * int(rate * len(words) * per_word))
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

"""Text-to-speech adapter, with two voice styles a video can pick:

- quick: Kokoro (default), Piper (lighter), or dummy (no models needed), from TTS_ENGINE.
  Clear, steady voices that are fast on any laptop.
- expressive: Chatterbox (optional, requirements-expressive.txt). It copies each character's
  reference clip and acts each line by its mood (moods.py). Slower; wants an NVIDIA GPU.

Every engine writes a mono 16-bit WAV. Models load once and are reused. Speech is kept
in a readable words-per-second window so the captions it drives stay readable: clips
outside it are time-stretched (pitch preserved) with FFmpeg.
"""

import functools
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

ENGINES = ("kokoro", "piper", "dummy")  # quick-style engines (TTS_ENGINE)
VOICE_STYLES = ("quick", "expressive")
DEFAULT_KOKORO_VOICE = "am_michael"

# Readable caption pace (words per second). Changing these re-synthesizes cached clips.
MIN_WPS, MAX_WPS, TARGET_WPS = 2.5, 3.0, 2.75
# Acted lines may run a little slower or faster than read ones and stay readable.
EXPRESSIVE_WPS = (2.2, 3.3)
# Very short lines ("Wait, what?") are mostly silence padding; their rate isn't meaningful.
MIN_WORDS_TO_PACE = 4

# Expressive: how strongly each mood is acted (Chatterbox "exaggeration", 0.25-2). The values
# sit close together so the voice moves gently from line to line instead of jumping.
EXPRESSIVE_INTENSITY = {
    "bored": 0.40, "curious": 0.50, "gets": 0.65, "hyped": 0.65,
    "chill": 0.45, "explain": 0.50, "think": 0.45, "laugh": 0.60,
}  # fmt: skip
EXPRESSIVE_CFG = 0.5  # how closely it follows the reference's pacing


class TTSError(RuntimeError):
    pass


_lock = threading.Lock()
_kokoro_pipelines: dict[str, object] = {}
_piper_voices: dict[str, object] = {}
_chatterbox: dict[str, object] = {}  # "model", plus prepared voices keyed by reference path


def engine_for(style: str, settings: Settings) -> str:
    return "chatterbox" if style == "expressive" else settings.tts_engine


def voice_for(character: Character, settings: Settings, style: str = "quick") -> str:
    engine = engine_for(style, settings)
    if engine == "dummy":
        return character.role
    voice = character.voices.get(engine)
    if engine == "kokoro":
        return voice or DEFAULT_KOKORO_VOICE
    if engine == "chatterbox":
        if not voice:
            raise TTSError(
                f"No expressive voice set for {character.name} (voices.chatterbox in the manifest)"
            )
        return str(settings.assets_dir / "characters" / voice)
    if not voice:
        raise TTSError(f"No Piper voice set for {character.name} (see PIPER_VOICE_A/B)")
    return voice


def _pace_window(style: str) -> tuple[float, float]:
    return EXPRESSIVE_WPS if style == "expressive" else (MIN_WPS, MAX_WPS)


def audio_key(
    text: str, character: Character, settings: Settings, style: str = "quick", mood: str | None = None
) -> str:
    """Identifies a synthesized clip, so unchanged lines reuse cached audio.

    Expressive clips also depend on the line's mood: a line moved to the end (Bunso's recall)
    is acted differently, so it gets new audio.
    """
    engine = engine_for(style, settings)
    acted = f"|{mood}@{EXPRESSIVE_INTENSITY.get(mood or '', 0.5)}" if engine == "chatterbox" else ""
    shift = (
        f"|shift{character.pitch_shift}" if character.pitch_shift and engine in ("kokoro", "piper") else ""
    )
    pace = "pace-{}-{}{}".format(*_pace_window(style), "-edge" if style == "expressive" else "")
    raw = f"{engine}|{voice_for(character, settings, style)}{shift}{acted}|{pace}|{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / float(wav.getframerate())


def synthesize(
    text: str,
    character: Character,
    out_path: Path,
    settings: Settings,
    style: str = "quick",
    mood: str | None = None,
) -> float:
    """Synthesize `text` to `out_path` in the given voice style and return the duration in seconds."""
    engine = engine_for(style, settings)
    if style not in VOICE_STYLES:
        raise TTSError(f"Unknown voice style '{style}' (use one of {VOICE_STYLES})")
    if engine not in (*ENGINES, "chatterbox"):
        raise TTSError(f"Unknown TTS_ENGINE '{settings.tts_engine}' (use one of {ENGINES})")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    voice = voice_for(character, settings, style)
    with _lock:
        if engine == "kokoro":
            _kokoro(text, voice, out_path)
        elif engine == "piper":
            _piper(text, voice, out_path, settings)
        elif engine == "chatterbox":
            seed = int(audio_key(text, character, settings, style, mood), 16) % 2**31
            _chatterbox_speak(text, Path(voice), mood, seed, out_path, settings)
        else:
            _dummy(text, character, out_path)
    if character.pitch_shift and engine in ("kokoro", "piper"):
        shift_pitch(out_path, character.pitch_shift, settings)
    pace_clip(out_path, len(text.split()), settings, _pace_window(style), nearest_edge=style == "expressive")
    return wav_duration(out_path)


def speech_rate(path: Path, word_count: int) -> float:
    return word_count / max(wav_duration(path), 0.01)


def _ffmpeg_filter(path: Path, audio_filter: str, settings: Settings, what: str) -> None:
    """Apply an FFmpeg audio filter in place. These are improvements, not requirements:
    if FFmpeg fails, the original clip is kept."""
    tmp = path.with_suffix(".tmp.wav")
    try:
        subprocess.run(
            [
                settings.ffmpeg_path, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(path), "-filter:a", audio_filter, "-c:a", "pcm_s16le", str(tmp),
            ],
            check=True,
            capture_output=True,
        )  # fmt: skip
        tmp.replace(path)
    except (OSError, subprocess.CalledProcessError) as exc:
        log.warning("Couldn't %s for %s: %s", what, path, exc)
        tmp.unlink(missing_ok=True)


def pace_clip(
    path: Path,
    word_count: int,
    settings: Settings,
    window: tuple[float, float] = (MIN_WPS, MAX_WPS),
    nearest_edge: bool = False,
) -> None:
    """Time-stretch a clip into the words-per-second window, keeping its pitch.

    Read lines go to the window's middle. Acted lines (`nearest_edge`) only go as far as the
    nearest edge, so a deliberately slow or fast delivery keeps as much of its feel as it can.
    """
    if word_count < MIN_WORDS_TO_PACE:
        return
    rate = speech_rate(path, word_count)
    if window[0] <= rate <= window[1]:
        return
    target = min(max(rate, window[0]), window[1]) if nearest_edge else sum(window) / 2
    # atempo > 1 speeds up; playing at target/rate turns `rate` into `target`.
    tempo = min(max(target / rate, 0.5), 2.0)
    _ffmpeg_filter(path, f"atempo={tempo:.4f}", settings, "adjust speech pace")


def shift_pitch(path: Path, semitones: float, settings: Settings) -> None:
    """Raise (or lower) a voice's pitch and formants together, which makes it sound like a
    smaller (younger) or bigger speaker rather than just higher. Needs FFmpeg with rubberband."""
    ratio = 2 ** (semitones / 12)
    _ffmpeg_filter(path, f"rubberband=pitch={ratio:.4f}:formant=shifted", settings, "shift the voice's pitch")


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


def _chatterbox_speak(
    text: str, reference: Path, mood: str | None, seed: int, out_path: Path, settings: Settings
) -> None:
    """Act one line in the reference clip's voice. Each reference is prepared once and reused;
    the seed comes from the line, so re-rendering an unchanged line gives the same take."""
    try:
        import soundfile as sf
        import torch
        from chatterbox.tts import ChatterboxTTS
    except ImportError as exc:
        raise TTSError(
            "Expressive voices aren't installed. Run: pip install -r requirements-expressive.txt"
        ) from exc
    if not reference.exists():
        raise TTSError(f"Expressive voice reference not found: {reference}")
    model = _chatterbox.get("model")
    if model is None:
        try:
            model = ChatterboxTTS.from_pretrained(device=settings.expressive_device)
        except (RuntimeError, AssertionError) as exc:  # e.g. no CUDA device
            raise TTSError(
                f"Couldn't start expressive voices on '{settings.expressive_device}': {exc}"
            ) from exc
        _chatterbox["model"] = model
    key = str(reference)
    if key not in _chatterbox:
        model.prepare_conditionals(key)
        _chatterbox[key] = model.conds
    model.conds = _chatterbox[key]
    torch.manual_seed(seed)
    wav = model.generate(
        text, exaggeration=EXPRESSIVE_INTENSITY.get(mood or "", 0.5), cfg_weight=EXPRESSIVE_CFG
    )
    sf.write(str(out_path), wav.squeeze(0).cpu().numpy(), model.sr, subtype="PCM_16")


@functools.cache
def _expressive_check(device: str) -> tuple[bool, str]:
    if importlib.util.find_spec("chatterbox") is None:
        return False, "Not installed (pip install -r requirements-expressive.txt)"
    if device.startswith("cuda"):
        import torch

        if not torch.cuda.is_available():
            return False, "Needs an NVIDIA graphics card"
        return True, f"Chatterbox on {torch.cuda.get_device_name(0)}"
    return True, f"Chatterbox on {device} (slow)"


def expressive_status(settings: Settings) -> dict:
    """Whether this laptop can use the Expressive voice style. Checked once per device."""
    ok, detail = _expressive_check(settings.expressive_device)
    return {"ok": ok, "detail": detail}


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

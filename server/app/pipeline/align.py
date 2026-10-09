"""Word-level timestamps for a synthesized line.

Captions always show the script's words (not Whisper's transcription, which may
mishear names). Whisper supplies the timing: when its word count matches the
script, its timestamps are used one-to-one; otherwise the script words are
spread across the detected speech span, weighted by length. Without
faster-whisper, the whole clip is used as the span.
"""

import importlib.util
import logging
import threading
from dataclasses import asdict, dataclass
from pathlib import Path

from app.config import Settings
from app.pipeline.tts import wav_duration

log = logging.getLogger(__name__)

_lock = threading.Lock()
_model = None
_model_key: tuple | None = None


@dataclass
class Word:
    text: str
    start: float
    end: float

    def to_dict(self) -> dict:
        return asdict(self)


def whisper_available() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def _get_model(settings: Settings):
    global _model, _model_key
    key = (settings.whisper_model, settings.whisper_device, settings.whisper_compute_type)
    if _model is None or _model_key != key:
        from faster_whisper import WhisperModel

        _model = WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
            download_root=str(settings.models_dir / "whisper"),
        )
        _model_key = key
    return _model


def _whisper_words(audio_path: Path, settings: Settings) -> list[Word]:
    with _lock:
        model = _get_model(settings)
        segments, _ = model.transcribe(str(audio_path), language="en", word_timestamps=True)
        return [
            Word(w.word.strip(), float(w.start), float(w.end))
            for segment in segments
            for w in (segment.words or [])
            if w.word.strip()
        ]


def distribute(words: list[str], start: float, end: float) -> list[Word]:
    """Spread words across [start, end], each taking time proportional to its length."""
    if not words:
        return []
    weights = [len(w) + 2 for w in words]
    total = float(sum(weights))
    span = max(end - start, 0.05 * len(words))
    result, t = [], start
    for word, weight in zip(words, weights, strict=True):
        duration = span * weight / total
        result.append(Word(word, round(t, 3), round(t + duration, 3)))
        t += duration
    return result


def align(audio_path: Path, text: str, settings: Settings) -> list[Word]:
    script_words = text.split()
    duration = wav_duration(audio_path)
    detected: list[Word] = []
    if whisper_available():
        try:
            detected = _whisper_words(audio_path, settings)
        except Exception:  # alignment is best-effort; fall back to even spacing
            log.exception("faster-whisper failed on %s", audio_path)

    if detected and len(detected) == len(script_words):
        return [
            Word(script, round(d.start, 3), round(max(d.end, d.start + 0.05), 3))
            for script, d in zip(script_words, detected, strict=True)
        ]
    if detected:
        return distribute(script_words, detected[0].start, detected[-1].end)
    return distribute(script_words, 0.05, max(duration - 0.1, 0.1))

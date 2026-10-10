"""Video composition with the FFmpeg CLI.

Layout (1080x1920): background fills the frame, captions sit around the vertical
center, and both characters stand along the bottom edge, the explainer on the left
and the asker on the right. The speaker is full color and lifted; the listener is
dimmed, a little smaller and lower. Each line picks an expression for both of them.
See docs/design.md.
"""

import os
import random
import shutil
import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.assets import Background, Character
from app.config import Settings
from app.pipeline.align import Word
from app.pipeline.captions import Segment
from app.pipeline.moods import line_moods

LINE_GAP_S = 0.25

# Cast layout, from the mascot sheet's "In the video" frame. Fractions of the frame width
# (x, width) and of the cast area's height (how far the feet drop below the frame).
CAST_AREA = 0.44  # bottom share of the frame the characters stand in
CAST_SLOTS = {
    "explainer": {"x": -0.06, "width": 0.62, "drop": 0.10},
    "asker": {"x": 0.48, "width": 0.54, "drop": 0.08},
}
CHARACTER_ASPECT = 1.25  # the art is 4:5
LISTENER_SCALE = 0.94
LISTENER_SINK = 0.06  # share of the character's height the listener sits lower
LISTENER_OPACITY = 0.55


class RenderError(RuntimeError):
    pass


class RenderCanceled(Exception):
    pass


@dataclass
class TimelineLine:
    character: Character
    audio: Path
    duration: float
    words: list[Word]


def ffmpeg_status(settings: Settings) -> dict:
    path = shutil.which(settings.ffmpeg_path) or (
        settings.ffmpeg_path if Path(settings.ffmpeg_path).exists() else None
    )
    if not path:
        return {"ok": False, "detail": f"FFmpeg not found ('{settings.ffmpeg_path}')"}
    return {"ok": True, "detail": path}


def build_segments(lines: list[TimelineLine], gap: float = LINE_GAP_S) -> tuple[list[Segment], float]:
    segments, t = [], 0.0
    for line in lines:
        segments.append(
            Segment(
                speaker=line.character.name,
                color=line.character.color,
                start=round(t, 3),
                end=round(t + line.duration, 3),
                words=line.words,
            )
        )
        t += line.duration + gap
    total = max(t - gap, 0.5) + 0.6  # short tail so the last caption can be read
    return segments, round(total, 3)


@dataclass(frozen=True)
class CastShot:
    """How one character looks during part of the video."""

    character: Character
    mood: str
    speaking: bool
    start: float
    end: float


def cast_shots(segments: list[Segment], characters: list[Character], total: float) -> list[CastShot]:
    """Both characters' expression and speaking state, covering the whole video without gaps.

    Each line's look holds from its start until the next line starts, so nobody blinks out
    during the pauses. Characters without a slot (neither asker nor explainer) aren't shown.
    """
    by_name = {c.name: c for c in characters}
    cast = [c for c in characters if c.role in CAST_SLOTS]
    roles = [by_name[s.speaker].role if s.speaker in by_name else "" for s in segments]
    shots = []
    for i, (segment, (speaker_mood, listener_mood)) in enumerate(
        zip(segments, line_moods(roles), strict=True)
    ):
        start = 0.0 if i == 0 else segment.start
        end = segments[i + 1].start if i + 1 < len(segments) else total
        for character in cast:
            speaking = character.role == roles[i]
            mood = speaker_mood if speaking else listener_mood
            shots.append(CastShot(character, mood, speaking, start, end))
    return shots


def _cast_layers(
    shots: list[CastShot], w: int, h: int
) -> list[tuple[str, str, int, int, list[tuple[float, float]]]]:
    """One overlay per (character, expression, speaking): (image, filter, x, y, time ranges)."""
    groups: dict[tuple[str, str, bool], list[CastShot]] = {}
    for shot in shots:
        groups.setdefault((shot.character.id, shot.mood, shot.speaking), []).append(shot)
    order = list(CAST_SLOTS)  # explainer first, so the asker is drawn on top
    layers = []
    for (_, mood, speaking), group in sorted(
        groups.items(), key=lambda item: order.index(item[1][0].character.role)
    ):
        character = group[0].character
        image = character.image_for(mood)
        if image is None:
            continue
        slot = CAST_SLOTS[character.role]
        width = slot["width"] * w
        height = width * CHARACTER_ASPECT
        bottom = h + slot["drop"] * CAST_AREA * h
        scale = 1.0 if speaking else LISTENER_SCALE
        if not speaking:
            bottom += LISTENER_SINK * height
        out_w, out_h = round(width * scale / 2) * 2, round(height * scale / 2) * 2
        x = round(slot["x"] * w + (width - out_w) / 2)
        y = round(bottom - out_h)
        look = f"scale={out_w}:{out_h},format=rgba"
        if not speaking:
            look += f",colorchannelmixer=aa={LISTENER_OPACITY}"
        layers.append((image, look, x, y, [(s.start, s.end) for s in group]))
    return layers


def audio_mix_command(settings: Settings, wavs: list[Path], out: Path, gap: float = LINE_GAP_S) -> list[str]:
    """Concatenate per-line WAVs with a gap after each, then loudness-normalize."""
    cmd = [settings.ffmpeg_path, "-y", "-hide_banner", "-loglevel", "error"]
    for wav in wavs:
        cmd += ["-i", str(wav)]
    chains = [
        f"[{i}:a]aresample=24000,aformat=sample_fmts=s16:channel_layouts=mono,apad=pad_dur={gap}[a{i}]"
        for i in range(len(wavs))
    ]
    joined = "".join(f"[a{i}]" for i in range(len(wavs)))
    chains.append(f"{joined}concat=n={len(wavs)}:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[out]")
    return cmd + ["-filter_complex", ";".join(chains), "-map", "[out]", "-c:a", "pcm_s16le", str(out)]


def _filter_path(path: Path, cwd: Path) -> str:
    """A path usable inside an FFmpeg filter argument (relative avoids escaping 'C:')."""
    try:
        return Path(os.path.relpath(path, cwd)).as_posix()
    except ValueError:  # different drive on Windows
        return path.as_posix().replace(":", "\\:")


def _enable_expr(ranges: list[tuple[float, float]]) -> str:
    return "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in ranges)


def video_command(
    settings: Settings,
    background: Background,
    voice: Path,
    captions: Path,
    segments: list[Segment],
    characters: list[Character],
    total: float,
    out: Path,
    work_dir: Path,
) -> list[str]:
    w, h, fps = settings.render_width, settings.render_height, settings.render_fps
    cmd = [settings.ffmpeg_path, "-y", "-hide_banner", "-nostats", "-progress", "pipe:1"]

    if background.file is None:
        # No clip: the same gradient and "floor" band the app previews (VideoFrame).
        top, bottom = (c.lstrip("#") for c in background.gradient)
        cmd += [
            "-f", "lavfi", "-i",
            f"gradients=s={w}x{h}:r={fps}:c0=0x{top}:c1=0x{bottom}:x0=0:y0=0:x1=0:y1={h}:speed=0",
        ]  # fmt: skip
        floor_y = round(h * 0.64)
        bg_chain = f"[0:v]drawbox=x=0:y={floor_y}:w={w}:h={h - floor_y}:color=white@0.05:t=fill,setsar=1[bg]"
    else:
        offset = 0.0
        if background.duration_s and background.duration_s > total + 1:
            offset = random.uniform(0, background.duration_s - total - 1)
        cmd += ["-stream_loop", "-1", "-ss", f"{offset:.2f}", "-i", str(background.file)]
        bg_chain = (
            f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={fps}[bg]"
        )

    cmd += ["-i", str(voice)]
    chains = [bg_chain]
    current = "bg"
    input_index = 2
    for image, look, x, y, ranges in _cast_layers(cast_shots(segments, characters, total), w, h):
        cmd += ["-loop", "1", "-framerate", str(fps), "-i", image]
        chains.append(f"[{input_index}:v]{look}[c{input_index}]")
        chains.append(
            f"[{current}][c{input_index}]overlay=x={x}:y={y}:"
            f"shortest=1:enable='{_enable_expr(ranges)}'[v{input_index}]"
        )
        current = f"v{input_index}"
        input_index += 1

    fonts_dir = settings.assets_dir / "fonts"
    subtitles = f"subtitles=filename='{_filter_path(captions, work_dir)}'"
    if fonts_dir.is_dir():
        subtitles += f":fontsdir='{_filter_path(fonts_dir, work_dir)}'"
    chains.append(f"[{current}]{subtitles}[vout]")

    return cmd + [
        "-filter_complex", ";".join(chains),
        "-map", "[vout]", "-map", "1:a",
        "-t", f"{total:.3f}",
        "-r", str(fps),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart",
        str(out),
    ]  # fmt: skip


def run_ffmpeg(
    cmd: list[str],
    cwd: Path,
    log_path: Path,
    total: float | None = None,
    on_progress: Callable[[float], None] | None = None,
    cancel: threading.Event | None = None,
) -> None:
    """Run FFmpeg, reporting progress (0..1) from `-progress pipe:1` when `total` is given."""
    with log_path.open("a", encoding="utf-8") as log:
        log.write(subprocess.list2cmdline(cmd) + "\n\n")
        log.flush()
        try:
            proc = subprocess.Popen(
                cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=log, text=True, encoding="utf-8"
            )
        except FileNotFoundError as exc:
            raise RenderError(f"FFmpeg not found ('{cmd[0]}'). Set FFMPEG_PATH.") from exc
        assert proc.stdout is not None
        for line in proc.stdout:
            if cancel is not None and cancel.is_set():
                proc.kill()
                proc.wait()
                raise RenderCanceled()
            if total and on_progress and line.startswith("out_time_us="):
                try:
                    seconds = int(line.split("=", 1)[1]) / 1_000_000
                except ValueError:
                    continue
                on_progress(min(max(seconds / total, 0.0), 1.0))
        code = proc.wait()
        if cancel is not None and cancel.is_set():
            raise RenderCanceled()
    if code != 0:
        tail = log_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-6:]
        raise RenderError("FFmpeg failed: " + " | ".join(tail))

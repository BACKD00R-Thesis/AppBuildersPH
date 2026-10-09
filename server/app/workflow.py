"""The PDF -> script -> voices -> captions -> MP4 pipeline, step by step.

Functions here take a database session and update records as they go, so the app
can poll progress. They run on the job runner (jobs.py), not in request handlers.
"""

import json
import logging
import threading
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, select

from app.assets import Character, get_pair, load_backgrounds, load_characters
from app.config import Settings
from app.models import Line, Project, ProjectStatus, Render, RenderStatus
from app.pipeline import align, captions, render, script, tts

log = logging.getLogger(__name__)


def project_dir(settings: Settings, project_id: str) -> Path:
    return settings.projects_dir / project_id


def ordered_lines(session: Session, project_id: str) -> list[Line]:
    return list(session.exec(select(Line).where(Line.project_id == project_id).order_by(Line.position)))


def characters_by_id(settings: Settings) -> dict[str, Character]:
    return {c.id: c for c in load_characters(settings)}


# --- Script -----------------------------------------------------------------


def generate_script(session: Session, project_id: str, settings: Settings) -> None:
    project = session.get(Project, project_id)
    if project is None:
        return
    try:
        asker, explainer = get_pair(load_characters(settings))
        result = script.generate_script(project.extracted_text, asker, explainer, settings)
    except (script.ScriptError, RuntimeError) as exc:
        # Keep an existing script editable if a regeneration fails.
        has_lines = bool(ordered_lines(session, project_id))
        project.status = ProjectStatus.SCRIPTED if has_lines else ProjectStatus.FAILED
        project.error = str(exc)
        project.updated_at = datetime.now(UTC)
        session.add(project)
        session.commit()
        return

    for old in ordered_lines(session, project_id):
        session.delete(old)
    for i, line in enumerate(result.lines):
        session.add(Line(project_id=project_id, position=i, character_id=line.character_id, text=line.text))
    if result.title and project.title.lower().endswith(".pdf"):
        project.title = result.title
    project.status = ProjectStatus.SCRIPTED
    project.error = None
    project.updated_at = datetime.now(UTC)
    session.add(project)
    session.commit()


# --- Voices and captions -----------------------------------------------------


def ensure_line_audio(session: Session, line: Line, character: Character, settings: Settings) -> Path:
    """Synthesize a line's audio unless an up-to-date clip is cached."""
    key = tts.audio_key(line.text, character, settings)
    if line.audio_key == key and line.audio_path and Path(line.audio_path).exists():
        return Path(line.audio_path)
    path = project_dir(settings, line.project_id) / "audio" / f"{line.id}-{key}.wav"
    if not path.exists():
        tts.synthesize(line.text, character, path, settings)
    if line.audio_path and line.audio_path != str(path):
        Path(line.audio_path).unlink(missing_ok=True)
        Path(line.audio_path).with_suffix(".words.json").unlink(missing_ok=True)
    line.audio_path = str(path)
    line.audio_key = key
    session.add(line)
    session.commit()
    return path


def line_words(audio: Path, text: str, settings: Settings) -> list[align.Word]:
    """Word timestamps for a clip, cached next to the audio."""
    cache = audio.with_suffix(".words.json")
    if cache.exists():
        return [align.Word(**w) for w in json.loads(cache.read_text(encoding="utf-8"))]
    words = align.align(audio, text, settings)
    cache.write_text(json.dumps([w.to_dict() for w in words]), encoding="utf-8")
    return words


# --- Render -----------------------------------------------------------------

# Share of the progress bar for each step.
STEPS = {"voices": (0.0, 0.45), "captions": (0.45, 0.6), "mixing": (0.6, 0.65), "rendering": (0.65, 1.0)}


def run_render(session: Session, render_id: str, settings: Settings, cancel: threading.Event) -> None:
    job = session.get(Render, render_id)
    if job is None or job.status == RenderStatus.CANCELED:
        return

    def update(phase: str, fraction: float = 0.0, **fields) -> None:
        lo, hi = STEPS[phase]
        job.step = phase
        job.progress = round(lo + (hi - lo) * fraction, 4)
        job.updated_at = datetime.now(UTC)
        for name, value in fields.items():
            setattr(job, name, value)
        session.add(job)
        session.commit()

    def check_cancel() -> None:
        if cancel.is_set():
            raise render.RenderCanceled()

    work_dir = project_dir(settings, job.project_id) / "renders" / job.id
    work_dir.mkdir(parents=True, exist_ok=True)
    log_path = work_dir / "render.log"

    try:
        update("voices", status=RenderStatus.RUNNING)
        lines = ordered_lines(session, job.project_id)
        if not lines:
            raise render.RenderError("The script is empty. Generate or write some lines first.")
        cast = characters_by_id(settings)
        backgrounds = {b.id: b for b in load_backgrounds(settings)}
        background = backgrounds.get(job.style_options.get("background_id", "")) or next(
            iter(backgrounds.values())
        )

        audios = []
        for i, line in enumerate(lines):
            check_cancel()
            character = cast.get(line.character_id)
            if character is None:
                raise render.RenderError(f"Unknown character '{line.character_id}'")
            audios.append((line, character, ensure_line_audio(session, line, character, settings)))
            update("voices", (i + 1) / len(lines))

        timeline = []
        for i, (line, character, audio) in enumerate(audios):
            check_cancel()
            words = line_words(audio, line.text, settings)
            timeline.append(render.TimelineLine(character, audio, tts.wav_duration(audio), words))
            update("captions", (i + 1) / len(audios))

        segments, total = render.build_segments(timeline)
        captions_path = work_dir / "captions.ass"
        captions_path.write_text(
            captions.build_ass(segments, settings.render_width, settings.render_height),
            encoding="utf-8",
        )

        check_cancel()
        update("mixing")
        voice_path = work_dir / "voice.wav"
        render.run_ffmpeg(
            render.audio_mix_command(settings, [t.audio for t in timeline], voice_path),
            cwd=work_dir,
            log_path=log_path,
            cancel=cancel,
        )

        update("rendering")
        out_path = work_dir / "video.mp4"
        render.run_ffmpeg(
            render.video_command(
                settings, background, voice_path, captions_path, segments,
                list(cast.values()), total, out_path, work_dir,
            ),
            cwd=work_dir,
            log_path=log_path,
            total=total,
            on_progress=lambda f: update("rendering", f),
            cancel=cancel,
        )  # fmt: skip
        update(
            "rendering", 1.0,
            status=RenderStatus.DONE, output_path=str(out_path), duration_s=total, step="done",
        )  # fmt: skip
    except render.RenderCanceled:
        job.status = RenderStatus.CANCELED
        job.updated_at = datetime.now(UTC)
        session.add(job)
        session.commit()
    except Exception as exc:  # report every failure to the app instead of crashing the worker
        log.exception("Render %s failed", render_id)
        job.status = RenderStatus.FAILED
        job.error = str(exc) or exc.__class__.__name__
        job.updated_at = datetime.now(UTC)
        session.add(job)
        session.commit()

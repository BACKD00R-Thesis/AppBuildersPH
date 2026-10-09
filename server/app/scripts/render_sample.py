"""Run the whole pipeline on a PDF from the command line and print the MP4 path.

Usage: python -m app.scripts.render_sample path/to/file.pdf [--pages 1-5] [--background parkour]
       python -m app.scripts.render_sample --script lines.txt   (skip the LLM; "Name: text" per line)
"""

import argparse
import threading
from pathlib import Path

from sqlmodel import Session

from app import workflow
from app.assets import load_characters
from app.config import get_settings
from app.db import get_engine, init_db
from app.models import Line, Project, ProjectStatus, Render, RenderStatus
from app.pipeline.extract import extract_pdf


def _lines_from_file(path: Path, project_id: str) -> list[Line]:
    by_name = {}
    for c in load_characters(get_settings()):
        by_name[c.name.lower()] = c.id
        by_name[c.id.lower()] = c.id
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if ":" not in raw:
            continue
        name, text = raw.split(":", 1)
        character_id = by_name.get(name.strip().lower())
        if character_id is None:
            raise SystemExit(f"Unknown speaker '{name.strip()}' in {path}")
        lines.append(
            Line(project_id=project_id, position=len(lines), character_id=character_id, text=text.strip())
        )
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, nargs="?")
    parser.add_argument("--pages")
    parser.add_argument("--script", type=Path, help="text file of 'Name: line' to use instead of the LLM")
    parser.add_argument("--background", default="parkour")
    args = parser.parse_args()
    if not args.pdf and not args.script:
        parser.error("give a PDF, --script, or both")

    settings = get_settings()
    init_db()
    with Session(get_engine()) as session:
        text, pages = "", 0
        if args.pdf:
            extracted = extract_pdf(args.pdf.read_bytes(), args.pages, settings.max_pdf_pages)
            text, pages = extracted.text, extracted.page_count
        source = args.pdf or args.script
        project = Project(title=source.stem, pdf_path=str(source), page_count=pages, extracted_text=text)
        session.add(project)
        session.commit()

        if args.script:
            for line in _lines_from_file(args.script, project.id):
                session.add(line)
            project.status = ProjectStatus.SCRIPTED
            session.add(project)
            session.commit()
        else:
            print("Writing script with Ollama…")
            workflow.generate_script(session, project.id, settings)
            session.refresh(project)
            if project.status != ProjectStatus.SCRIPTED:
                raise SystemExit(f"Script failed: {project.error}")

        for line in workflow.ordered_lines(session, project.id):
            print(f"  [{line.character_id}] {line.text}")

        render = Render(project_id=project.id, style_options={"background_id": args.background})
        session.add(render)
        session.commit()
        print("Rendering…")
        workflow.run_render(session, render.id, settings, threading.Event())
        session.refresh(render)
        if render.status != RenderStatus.DONE:
            raise SystemExit(f"Render failed: {render.error}")
        print(f"Done ({render.duration_s:.1f}s): {render.output_path}")


if __name__ == "__main__":
    main()

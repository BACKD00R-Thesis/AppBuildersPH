"""Print the dialogue the LLM writes for a PDF, without saving or rendering anything.

Usage: python -m app.scripts.script_sample path/to/file.pdf [--pages 1-5]
"""

import argparse
from pathlib import Path

from app.assets import get_pair, load_characters
from app.config import get_settings
from app.pipeline.extract import extract_pdf
from app.pipeline.script import generate_script


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages")
    args = parser.parse_args()

    settings = get_settings()
    extracted = extract_pdf(args.pdf.read_bytes(), args.pages, settings.max_pdf_pages)
    print(f"Extracted {len(extracted.text)} characters from {extracted.page_count} pages\n")
    characters = load_characters(settings)
    names = {c.id: c.name for c in characters}
    asker, explainer = get_pair(characters)
    result = generate_script(extracted.text, asker, explainer, settings)
    print(f"# {result.title or '(untitled)'}\n")
    for line in result.lines:
        print(f"{names[line.character_id]}: {line.text}")


if __name__ == "__main__":
    main()

"""PDF to clean text with PyMuPDF."""

import re
from dataclasses import dataclass

import pymupdf


class ExtractError(ValueError):
    pass


@dataclass
class Extracted:
    text: str
    page_count: int


def parse_pages(spec: str | None, page_count: int) -> list[int]:
    """Parse a 1-based page selection like "1-3, 7" into 0-based indexes."""
    if not spec or not spec.strip():
        return list(range(page_count))
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        match = re.fullmatch(r"(\d+)\s*(?:-\s*(\d+))?", part)
        if not match:
            raise ExtractError(f"Invalid page selection: {part!r}")
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if start < 1 or end < start:
            raise ExtractError(f"Invalid page range: {part!r}")
        pages.update(range(start - 1, min(end, page_count)))
    if not pages:
        raise ExtractError("Page selection is outside the document")
    return sorted(pages)


def clean_text(raw: str) -> str:
    text = raw.replace("\r", "\n").replace("­", "")  # soft hyphens
    # Re-join words hyphenated across line breaks: "photo-\nsynthesis" -> "photosynthesis"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        # Drop bare page numbers and lone bullet glyphs.
        if not line or re.fullmatch(r"(page\s*)?\d{1,4}|[•▪◦·\-–—*]", line, flags=re.I):
            continue
        lines.append(line)
    text = " ".join(lines)
    return re.sub(r"\s{2,}", " ", text).strip()


def extract_pdf(data: bytes, pages: str | None, max_pages: int) -> Extracted:
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises several types for bad files
        raise ExtractError("That file isn't a readable PDF") from exc
    with doc:
        if doc.needs_pass:
            raise ExtractError("Password-protected PDFs aren't supported")
        selected = parse_pages(pages, doc.page_count)
        if len(selected) > max_pages:
            raise ExtractError(
                f"Selected {len(selected)} pages; the limit is {max_pages}. Pick a page range."
            )
        text = clean_text("\n".join(doc[i].get_text() for i in selected))
        if len(text) < 40:
            raise ExtractError(
                "Couldn't find text in this PDF. Scanned PDFs (images only) aren't supported yet."
            )
        return Extracted(text=text, page_count=doc.page_count)

"""Render the mascots' expressions to transparent PNGs with a headless Chromium browser.

Usage: python -m app.scripts.render_mascots
Reads each character's "design" (a Claude Design .dc.html file in assets/characters/design)
and writes one PNG per entry in its "moods" (assets/characters/manifest.json). Re-run it
after updating the design files. Needs Microsoft Edge or Google Chrome; set BROWSER_PATH
if yours isn't in a standard location.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.config import get_settings

WIDTH, HEIGHT = 800, 1000  # the designs are 4:5

BROWSERS = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)
BROWSER_NAMES = ("msedge", "google-chrome", "chromium", "chromium-browser", "chrome")

# The "?" and "!" in Bunso's expressions use the sheet's display font.
FONT_CSS = "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&display=swap"
PAGE = """<!doctype html><html><head><meta charset="utf-8">
<link href="{font}" rel="stylesheet">
<style>html,body{{margin:0;background:transparent;overflow:hidden}}.stage{{width:{w}px}}</style>
</head><body><div class="stage">{body}</div></body></html>"""

SC_IF = re.compile(r'<sc-if value="\{\{\s*(\w+)\s*\}\}"[^>]*>(.*?)</sc-if>', re.S)


def find_browser() -> str:
    candidates = [os.environ.get("BROWSER_PATH", ""), *BROWSERS]
    for path in candidates:
        if path and Path(path).exists():
            return path
    for name in BROWSER_NAMES:
        if found := shutil.which(name):
            return found
    raise SystemExit("No Edge or Chrome found. Set BROWSER_PATH to a Chromium-based browser.")


def mood_markup(design: str, mood: str) -> str:
    """The design's <x-dc> markup with only this mood's <sc-if> block (isChill, isGets, …) kept."""
    match = re.search(r"<x-dc>(.*)</x-dc>", design, re.S)
    if not match:
        raise SystemExit("Not a Claude Design file: no <x-dc> element")
    flag = "is" + mood[:1].upper() + mood[1:]
    return SC_IF.sub(lambda m: m.group(2) if m.group(1) == flag else "", match.group(1))


def screenshot(browser: str, html: str, out: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run(
            [
                browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--default-background-color=00000000", f"--window-size={WIDTH},{HEIGHT}",
                "--virtual-time-budget=4000", f"--user-data-dir={Path(tmp) / 'profile'}",
                f"--screenshot={out}", page.as_uri(),
            ],
            check=True,
            capture_output=True,
            timeout=60,
        )  # fmt: skip
    if not out.exists():
        raise SystemExit(f"The browser didn't write {out}")


def main() -> None:
    base = get_settings().assets_dir / "characters"
    browser = find_browser()
    for entry in json.loads((base / "manifest.json").read_text(encoding="utf-8")):
        if not entry.get("design"):
            continue
        design = (base / entry["design"]).read_text(encoding="utf-8")
        for mood, file in entry.get("moods", {}).items():
            out = base / file
            screenshot(browser, PAGE.format(font=FONT_CSS, w=WIDTH, body=mood_markup(design, mood)), out)
            print(f"  {entry['name']}: {mood} -> {out.name}")


if __name__ == "__main__":
    main()

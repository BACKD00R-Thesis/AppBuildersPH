"""Burned-in "brainrot" captions as an ASS subtitle file (styles from docs/design.md).

One to three words are on screen at a time; the word being spoken is highlighted
and slightly enlarged. The current speaker's name is shown above the character.
"""

import re
from dataclasses import dataclass

from app.pipeline.align import Word

CAPTION_FONT = "Montserrat ExtraBold"  # drop the TTF into assets/fonts; libass falls back otherwise
HIGHLIGHT = "#B6FF3B"
MAX_WORDS_PER_CHUNK = 3
HOLD_LAST_WORD_S = 0.25

# Layout for a 1080x1920 frame. Platform UI covers the bottom 320px and the right 140px.
CAPTION_Y = 1000  # just below the character, around the vertical center
SPEAKER_Y = 230


@dataclass
class Segment:
    """One script line placed on the video timeline."""

    speaker: str
    color: str
    start: float
    end: float
    words: list[Word]  # times relative to `start`


def ass_color(hex_color: str) -> str:
    """'#RRGGBB' -> ASS '&H00BBGGRR'."""
    value = hex_color.lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        value = "FFFFFF"
    r, g, b = value[0:2], value[2:4], value[4:6]
    return f"&H00{b}{g}{r}".upper()


def ass_time(seconds: float) -> str:
    centis = max(0, round(seconds * 100))
    h, rem = divmod(centis, 360000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def escape(text: str) -> str:
    return text.replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", " ")


def chunk_words(words: list[Word]) -> list[list[Word]]:
    """Group words into chunks of up to 3, breaking after punctuation."""
    chunks: list[list[Word]] = []
    current: list[Word] = []
    for word in words:
        current.append(word)
        if len(current) == MAX_WORDS_PER_CHUNK or re.search(r"[.,!?;:…]$", word.text):
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks


def _header(width: int, height: int) -> str:
    outline_black = "&H00000000"
    white = "&H00FFFFFF"
    return "\n".join(
        [
            "[Script Info]",
            "ScriptType: v4.00+",
            f"PlayResX: {width}",
            f"PlayResY: {height}",
            "WrapStyle: 0",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
            "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
            "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Caption,{CAPTION_FONT},92,{white},{white},{outline_black},&H80000000,"
            "-1,0,0,0,100,100,0,0,1,8,3,5,90,140,0,1",
            f"Style: Speaker,{CAPTION_FONT},58,{white},{white},{outline_black},&H80000000,"
            "-1,0,0,0,100,100,0,0,1,6,2,5,90,140,0,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]
    )


def build_ass(segments: list[Segment], width: int = 1080, height: int = 1920) -> str:
    x = (width - 140 + 90) // 2  # centered within the safe area
    highlight = ass_color(HIGHLIGHT)
    events: list[str] = []
    for segment in segments:
        events.append(
            f"Dialogue: 1,{ass_time(segment.start)},{ass_time(segment.end)},Speaker,,0,0,0,,"
            f"{{\\an5\\pos({x},{SPEAKER_Y})\\c{ass_color(segment.color)}}}"
            f"{escape(segment.speaker.upper())}"
        )
        for chunk in chunk_words(segment.words):
            for i, word in enumerate(chunk):
                start = segment.start + word.start
                if i + 1 < len(chunk):
                    end = segment.start + chunk[i + 1].start
                else:
                    end = min(segment.start + word.end + HOLD_LAST_WORD_S, segment.end)
                if end <= start:
                    end = start + 0.05
                parts = []
                for j, other in enumerate(chunk):
                    text = escape(other.text.upper())
                    if j == i:
                        parts.append(f"{{\\c{highlight}\\fscx112\\fscy112}}{text}{{\\r}}")
                    else:
                        parts.append(text)
                events.append(
                    f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,"
                    f"{{\\an5\\pos({x},{CAPTION_Y})}}{' '.join(parts)}"
                )
    return _header(width, height) + "\n" + "\n".join(events) + "\n"

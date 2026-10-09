"""Burned-in "brainrot" captions as an ASS subtitle file (styles from docs/design.md).

Captions show a block of up to two lines (up to three words each); extra words go
on the second line. The word being spoken is highlighted in mustard, the design's
one highlight. A block stays up until the next block starts, so two blocks are
never on screen at once. The current speaker's name is shown above the character.

Three styles match the app's "Captions" picker: bold-pop (outlined Archivo Black),
clean (plain sans on a soft dark box) and outline (hollow letters).
"""

import re
from dataclasses import dataclass

from app.pipeline.align import Word

# Fonts: drop the TTFs into assets/fonts; libass falls back to a system font otherwise.
CAPTION_FONT = "Archivo Black"
CLEAN_FONT = "Plus Jakarta Sans"
CAPTION_SIZE = 84
HIGHLIGHT = "#E8B23A"  # mustard
OUTLINE_COLOR = "#151A14"  # the video base color from the design
DEFAULT_STYLE = "bold-pop"
MAX_WORDS_PER_LINE = 3
MAX_CHARS_PER_LINE = 16  # what fits in the safe area at CAPTION_SIZE, uppercase
MAX_LINES = 2
HOLD_LAST_WORD_S = 0.4

# Layout for a 1080x1920 frame. Platform UI covers the bottom 320px and the right 140px.
CAPTION_Y = 1000  # center of the caption block, just below the character
SPEAKER_Y = 230

SENTENCE_END = re.compile(r"[.!?…]$")
CLAUSE_END = re.compile(r"[,;:]$")


@dataclass
class Segment:
    """One script line placed on the video timeline."""

    speaker: str
    color: str
    start: float
    end: float
    words: list[Word]  # times relative to `start`


Block = list[list[Word]]  # lines of words shown together


def ass_color(hex_color: str, alpha: int = 0) -> str:
    """'#RRGGBB' -> ASS '&HAABBGGRR' (alpha 0 = opaque, 255 = invisible)."""
    value = hex_color.lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        value = "FFFFFF"
    r, g, b = value[0:2], value[2:4], value[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


@dataclass(frozen=True)
class CaptionLook:
    font: str
    size: int
    fill: str  # ASS colors
    outline_color: str
    border_style: int  # 1 = outline + shadow, 3 = opaque box (box uses outline_color)
    outline: int
    shadow: int
    # Override tags for the word being spoken
    active: str


def caption_look(style: str) -> CaptionLook:
    mustard = ass_color(HIGHLIGHT)
    if style == "clean":
        return CaptionLook(
            font=CLEAN_FONT, size=70, fill=ass_color("#FFFFFF"),
            outline_color=ass_color(OUTLINE_COLOR, alpha=0x50), border_style=3, outline=14, shadow=0,
            active=f"\\c{mustard}",
        )  # fmt: skip
    if style == "outline":
        # Hollow white letters; the active word fills in mustard.
        return CaptionLook(
            font=CAPTION_FONT, size=CAPTION_SIZE, fill=ass_color("#FFFFFF", alpha=0xFF),
            outline_color=ass_color("#FFFFFF"), border_style=1, outline=4, shadow=0,
            active=f"\\1a&H00&\\c{mustard}\\3c{ass_color(OUTLINE_COLOR)}",
        )  # fmt: skip
    return CaptionLook(
        font=CAPTION_FONT, size=CAPTION_SIZE, fill=ass_color("#FFFFFF"),
        outline_color=ass_color(OUTLINE_COLOR), border_style=1, outline=7, shadow=3,
        active=f"\\c{mustard}",
    )  # fmt: skip


def ass_time(seconds: float) -> str:
    centis = max(0, round(seconds * 100))
    h, rem = divmod(centis, 360000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def escape(text: str) -> str:
    return text.replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", " ")


def _line_fits(line: list[Word], word: Word) -> bool:
    if len(line) >= MAX_WORDS_PER_LINE:
        return False
    chars = sum(len(w.text) for w in line) + len(line) + len(word.text)
    return not line or chars <= MAX_CHARS_PER_LINE


def chunk_words(words: list[Word]) -> list[Block]:
    """Group words into blocks of up to two lines.

    A line ends when it's full (3 words or 16 characters) or after a comma; a
    block ends after its second line or at the end of a sentence.
    """
    blocks: list[Block] = []
    block: Block = []
    line: list[Word] = []

    def end_line() -> None:
        nonlocal line
        if line:
            block.append(line)
            line = []

    def end_block() -> None:
        nonlocal block
        end_line()
        if block:
            blocks.append(block)
            block = []

    for word in words:
        if line and not _line_fits(line, word):
            end_line()
            if len(block) == MAX_LINES:
                end_block()
        line.append(word)
        if SENTENCE_END.search(word.text):
            end_block()
        elif CLAUSE_END.search(word.text):
            end_line()
            if len(block) == MAX_LINES:
                end_block()
    end_block()
    return blocks


def _header(width: int, height: int, look: CaptionLook) -> str:
    dark = ass_color(OUTLINE_COLOR)
    white = ass_color("#FFFFFF")
    return "\n".join(
        [
            "[Script Info]",
            "ScriptType: v4.00+",
            f"PlayResX: {width}",
            f"PlayResY: {height}",
            "WrapStyle: 2",  # only break lines where we put \N
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
            "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
            "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Caption,{look.font},{look.size},{look.fill},{look.fill},{look.outline_color},&H80000000,"
            f"-1,0,0,0,100,100,0,0,{look.border_style},{look.outline},{look.shadow},5,90,140,0,1",
            f"Style: Speaker,{CAPTION_FONT},58,{white},{white},{dark},&H80000000,"
            "-1,0,0,0,100,100,0,0,1,6,2,5,90,140,0,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]
    )


def _block_text(block: Block, active: Word, active_tags: str) -> str:
    lines = []
    for line in block:
        parts = []
        for word in line:
            text = escape(word.text.upper())
            parts.append(f"{{{active_tags}}}{text}{{\\r}}" if word is active else text)
        lines.append(" ".join(parts))
    return "\\N".join(lines)


def build_ass(
    segments: list[Segment], width: int = 1080, height: int = 1920, style: str = DEFAULT_STYLE
) -> str:
    x = (width - 140 + 90) // 2  # centered within the safe area
    look = caption_look(style)
    events: list[str] = []
    for segment in segments:
        events.append(
            f"Dialogue: 1,{ass_time(segment.start)},{ass_time(segment.end)},Speaker,,0,0,0,,"
            f"{{\\an5\\pos({x},{SPEAKER_Y})\\c{ass_color(segment.color)}}}"
            f"{escape(segment.speaker.upper())}"
        )
        blocks = chunk_words(segment.words)
        for b, block in enumerate(blocks):
            words = [w for line in block for w in line]
            next_block_start = blocks[b + 1][0][0].start if b + 1 < len(blocks) else None
            for i, word in enumerate(words):
                start = segment.start + word.start
                if i + 1 < len(words):
                    end = segment.start + words[i + 1].start
                elif next_block_start is not None:
                    end = segment.start + next_block_start  # hand over without overlap
                else:
                    end = min(segment.start + word.end + HOLD_LAST_WORD_S, segment.end)
                if end <= start:
                    end = start + 0.05
                events.append(
                    f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,"
                    f"{{\\an5\\pos({x},{CAPTION_Y})}}{_block_text(block, word, look.active)}"
                )
    return _header(width, height, look) + "\n" + "\n".join(events) + "\n"

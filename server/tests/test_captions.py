import re

from app.pipeline.align import Word, distribute
from app.pipeline.captions import Segment, ass_color, ass_time, build_ass, chunk_words


def words_of(text: str, wps: float = 2.75) -> list[Word]:
    return [Word(t, round(i / wps, 3), round((i + 1) / wps, 3)) for i, t in enumerate(text.split())]


def block_texts(text: str) -> list[list[str]]:
    return [[" ".join(w.text for w in line) for line in block] for block in chunk_words(words_of(text))]


def parse_time(value: str) -> float:
    h, m, s = value.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def caption_events(ass: str) -> list[tuple[float, float, str]]:
    events = []
    for line in ass.splitlines():
        if line.startswith("Dialogue: 0,"):
            _, start, end, *_rest = line.split(",", 9)
            events.append((parse_time(start), parse_time(end), line.split(",", 9)[9]))
    return events


def test_ass_color_is_bgr():
    assert ass_color("#B6FF3B") == "&H003BFFB6"
    assert ass_color("nonsense") == "&H00FFFFFF"


def test_ass_time():
    assert ass_time(0) == "0:00:00.00"
    assert ass_time(61.234) == "0:01:01.23"
    assert ass_time(3725.5) == "1:02:05.50"


def test_blocks_put_extra_words_on_a_second_line():
    assert block_texts("plants eat light every single day and night") == [
        ["plants eat light", "every single day"],
        ["and night"],
    ]


def test_blocks_end_at_sentences_and_lines_end_at_commas():
    assert block_texts("Wait, cats eat fish? Yes. They really do") == [
        ["Wait,", "cats eat fish?"],
        ["Yes."],
        ["They really do"],
    ]


def test_long_words_get_their_own_line():
    # Over 16 characters per line, so each long word takes a line of its own.
    assert block_texts("photosynthesis transforms electromagnetic radiation") == [
        ["photosynthesis", "transforms"],
        ["electromagnetic", "radiation"],
    ]


def test_distribute_covers_span_in_order():
    words = distribute(["a", "longer", "word"], 1.0, 3.0)
    assert words[0].start == 1.0
    assert abs(words[-1].end - 3.0) < 0.01
    assert all(a.end <= b.start + 1e-6 for a, b in zip(words, words[1:], strict=False))
    assert (words[1].end - words[1].start) > (words[0].end - words[0].start)


def test_build_ass_two_lines_with_one_highlighted_word():
    segment = Segment(
        speaker="Dex", color="#3BC8FF", start=2.0, end=5.0, words=words_of("Plants eat {light} every day")
    )
    ass = build_ass([segment])
    assert "WrapStyle: 2" in ass
    speaker, *captions = [line for line in ass.splitlines() if line.startswith("Dialogue:")]
    assert "DEX" in speaker
    assert len(captions) == 5  # one event per word
    first = captions[0]
    assert first.startswith("Dialogue: 0,0:00:02.00,0:00:02.36,Caption")
    assert "\\N" in first  # two lines
    assert first.count("\\c&H003AB2E8") == 1  # mustard
    assert "}PLANTS{" in first
    assert "{LIGHT}" not in ass and "(LIGHT)" in ass  # braces escaped
    assert "fscx" not in ass  # no size change on the active word


def test_caption_styles():
    segment = Segment("Dex", "#3BC8FF", 0.0, 2.0, words_of("Light in, sugar out."))
    bold = build_ass([segment], style="bold-pop")
    assert "Style: Caption,Archivo Black,84,&H00FFFFFF" in bold
    clean = build_ass([segment], style="clean")
    assert "Style: Caption,Plus Jakarta Sans,70" in clean and ",3,14,0,5," in clean  # soft box
    outline = build_ass([segment], style="outline")
    assert "Style: Caption,Archivo Black,84,&HFFFFFFFF" in outline  # hollow fill
    assert "\\1a&H00&" in outline  # active word fills in


def test_caption_events_never_overlap():
    segments = [
        Segment(
            "Dex", "#3BC8FF", 0.0, 4.0, words_of("Wait, plants literally eat sunlight every single day?")
        ),
        Segment(
            "Nova",
            "#FFB23B",
            4.25,
            9.0,
            words_of("Basically. Chlorophyll is a solar panel that pays in sugar."),
        ),
    ]
    events = caption_events(build_ass(segments))
    assert len(events) == 18
    for (_, end, _), (start, _, _) in zip(events, events[1:], strict=False):
        assert end <= start + 1e-6


def test_caption_lines_stay_within_three_words():
    segment = Segment(
        "Dex", "#3BC8FF", 0.0, 10.0, words_of("one two three four five six seven eight nine ten")
    )
    for _, _, text in caption_events(build_ass([segment])):
        plain = re.sub(r"\{[^}]*\}", "", text)
        lines = plain.split("\\N")
        assert len(lines) <= 2
        assert all(len(line.split()) <= 3 for line in lines)

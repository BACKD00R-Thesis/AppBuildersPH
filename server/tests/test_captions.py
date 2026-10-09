from app.pipeline.align import Word, distribute
from app.pipeline.captions import Segment, ass_color, ass_time, build_ass, chunk_words


def test_ass_color_is_bgr():
    assert ass_color("#B6FF3B") == "&H003BFFB6"
    assert ass_color("nonsense") == "&H00FFFFFF"


def test_ass_time():
    assert ass_time(0) == "0:00:00.00"
    assert ass_time(61.234) == "0:01:01.23"
    assert ass_time(3725.5) == "1:02:05.50"


def test_chunk_words_breaks_on_punctuation_and_size():
    words = [Word(t, 0, 0) for t in "Wait, plants eat light every single day".split()]
    assert [[w.text for w in c] for c in chunk_words(words)] == [
        ["Wait,"],
        ["plants", "eat", "light"],
        ["every", "single", "day"],
    ]


def test_distribute_covers_span_in_order():
    words = distribute(["a", "longer", "word"], 1.0, 3.0)
    assert words[0].start == 1.0
    assert abs(words[-1].end - 3.0) < 0.01
    assert all(a.end <= b.start + 1e-6 for a, b in zip(words, words[1:], strict=False))
    assert (words[1].end - words[1].start) > (words[0].end - words[0].start)


def test_build_ass_highlights_one_word_per_event():
    segment = Segment(
        speaker="Dex",
        color="#3BC8FF",
        start=2.0,
        end=3.0,
        words=[Word("Plants", 0.0, 0.4), Word("eat", 0.4, 0.6), Word("{light}", 0.6, 0.9)],
    )
    ass = build_ass([segment])
    events = [line for line in ass.splitlines() if line.startswith("Dialogue:")]
    assert len(events) == 4  # speaker label + one event per word
    assert "DEX" in events[0]
    assert events[1].startswith("Dialogue: 0,0:00:02.00,0:00:02.40,Caption")
    assert "\\c&H003BFFB6" in events[2] and "}EAT{" in events[2]
    assert "{LIGHT}" not in ass and "(LIGHT)" in ass  # braces escaped

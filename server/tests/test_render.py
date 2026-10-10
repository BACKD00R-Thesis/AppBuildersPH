from app.assets import Character
from app.pipeline.captions import Segment
from app.pipeline.render import cast_shots

TITO = Character(id="tito-boy", name="Tito", role="explainer", persona="warm", color="#F08A3C")
BUNSO = Character(id="bunso", name="Bunso", role="asker", persona="curious", color="#F27BA5")


def segments(*speakers: str) -> list[Segment]:
    return [
        Segment(name, "#FFFFFF", start=i * 2.0, end=i * 2.0 + 1.5, words=[])
        for i, name in enumerate(speakers)
    ]


def looks(shots, character):
    return [(s.mood, s.speaking) for s in shots if s.character is character]


def test_cast_follows_the_hook_explain_recall_loop():
    shots = cast_shots(segments("Bunso", "Tito", "Bunso", "Tito", "Tito", "Bunso"), [TITO, BUNSO], total=12.0)
    assert looks(shots, BUNSO) == [
        ("bored", True),  # the hook
        ("curious", False),
        ("curious", True),
        ("curious", False),
        ("hyped", False),  # Tito's last line, the dad joke
        ("gets", True),  # the recall
    ]
    assert looks(shots, TITO) == [
        ("chill", False),
        ("explain", True),
        ("chill", False),
        ("explain", True),
        ("laugh", True),
        ("chill", False),
    ]


def test_cast_covers_the_pauses_between_lines():
    shots = [
        s
        for s in cast_shots(segments("Bunso", "Tito", "Bunso"), [TITO, BUNSO], total=6.5)
        if s.character is TITO
    ]
    assert [(s.start, s.end) for s in shots] == [(0.0, 2.0), (2.0, 4.0), (4.0, 6.5)]


def test_cast_skips_characters_without_a_slot():
    narrator = Character(id="n", name="Narrator", role="narrator", persona="", color="#FFFFFF")
    shots = cast_shots(segments("Bunso", "Tito"), [TITO, BUNSO, narrator], total=4.0)
    assert {s.character.id for s in shots} == {"tito-boy", "bunso"}

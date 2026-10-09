import json

import httpx
import pytest

from app.assets import Character
from app.config import get_settings
from app.pipeline.script import (
    ScriptError,
    ScriptLine,
    ScriptOptions,
    build_prompt,
    check_lines,
    generate_script,
    parse_ideas,
    parse_lines,
)

ASKER = Character(id="tito-boy", name="Tito Boy", role="asker", persona="loud", color="#D5E3D7")
EXPLAINER = Character(id="bunso", name="Bunso", role="explainer", persona="smug", color="#8FB59E")

IDEAS = json.dumps(
    {
        "title": "Photosynthesis",
        "subject": "Biology",
        "key_ideas": ["plants turn light into sugar", "Chlorophyll absorbs light", "Water is split"],
    }
)


def lines_json(n: int = 6) -> str:
    lines = [{"speaker": "A" if i % 2 == 0 else "B", "text": f"Line number {i}."} for i in range(n)]
    return json.dumps({"lines": lines})


def test_parse_ideas_cleans_and_limits():
    ideas = parse_ideas(IDEAS, ScriptOptions(length_s=30))
    assert ideas.title == "Photosynthesis"
    assert ideas.subject == "Biology"
    assert ideas.key_ideas[0] == "Plants turn light into sugar"  # capitalized
    assert len(ideas.key_ideas) == 3


def test_parse_ideas_requires_ideas():
    with pytest.raises(ScriptError):
        parse_ideas(json.dumps({"title": "x", "key_ideas": []}))


def test_parse_lines_maps_speakers():
    lines = parse_lines(lines_json(), ASKER, EXPLAINER)
    assert [line.character_id for line in lines[:2]] == ["tito-boy", "bunso"]
    assert len(lines) == 6


def test_parse_lines_recovers_json_wrapped_in_prose():
    raw = "Sure! Here you go:\n```json\n" + lines_json() + "\n```"
    assert len(parse_lines(raw, ASKER, EXPLAINER)) == 6


def test_parse_lines_cleans_text():
    raw = json.dumps(
        {
            "lines": [
                {"speaker": "Tito Boy", "text": 'Tito Boy: "Wait, plants eat light?" (gasps)'},
                {"speaker": "bunso", "text": "B: *sighs* Yes,   basically."},
                {"speaker": "???", "text": "Unknown speakers alternate."},
                {"speaker": "A", "text": "   "},
                {"speaker": "B", "text": "Ok."},
            ]
        }
    )
    lines = parse_lines(raw, ASKER, EXPLAINER)
    assert lines[0].text == "Wait, plants eat light?"
    assert lines[1].text == "Yes, basically."
    assert lines[2].character_id == "tito-boy"  # previous was the explainer
    assert len(lines) == 4  # empty line dropped


def test_parse_lines_fixes_self_address():
    raw = json.dumps(
        {
            "lines": [
                {"speaker": "A", "text": "Tito Boy, how do cells make energy?"},
                {"speaker": "B", "text": "It's like cooking, Bunso. Easy!"},
                {"speaker": "A", "text": "Talaga, Tito Boy?"},
                {"speaker": "B", "text": "Bunso knows best, Tito Boy."},
            ]
        }
    )
    texts = [line.text for line in parse_lines(raw, ASKER, EXPLAINER)]
    assert texts == [
        "Bunso, how do cells make energy?",
        "It's like cooking, Tito Boy. Easy!",
        "Talaga, Bunso?",
        "Bunso knows best, Tito Boy.",  # third-person mentions are left alone
    ]


def test_parse_lines_rejects_too_few_lines():
    with pytest.raises(ScriptError, match="usable lines"):
        parse_lines(lines_json(2), ASKER, EXPLAINER)


def test_check_lines_drops_repeats():
    lines = [ScriptLine("tito-boy", t) for t in ["One.", "Two!", "one", "Three.", "Four."]]
    assert [line.text for line in check_lines(lines)] == ["One.", "Two!", "Three.", "Four."]


def test_build_prompt_uses_length_ideas_and_language():
    prompt = build_prompt(
        "Sentence. " * 5000, ASKER, EXPLAINER, ["Idea one"], ScriptOptions(90, taglish=False)
    )
    assert "Tito Boy" in prompt and "Bunso" in prompt
    assert "1. Idea one" in prompt
    assert "about 90 seconds" in prompt
    assert "English only" in prompt
    assert len(prompt) < 12000
    assert "Taglish" in build_prompt("Text.", ASKER, EXPLAINER, options=ScriptOptions(taglish=True))


def _client(handler) -> httpx.Client:
    return httpx.Client(base_url="http://ollama.test", transport=httpx.MockTransport(handler))


def test_generate_script_runs_ideas_then_dialogue_with_retry():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body)
        if "key_ideas" in body["format"]["properties"]:
            content = IDEAS
        else:
            content = (
                "garbage" if sum("lines" in c["format"]["properties"] for c in calls) == 1 else lines_json()
            )
        return httpx.Response(200, json={"message": {"content": content}})

    steps = []
    result = generate_script(
        "material", ASKER, EXPLAINER, get_settings(), client=_client(handler), on_step=steps.append
    )
    assert steps == ["ideas", "jokes", "check"]
    assert len(calls) == 3  # ideas, failed dialogue, retried dialogue
    assert "1. Plants turn light into sugar" in calls[1]["messages"][0]["content"]
    assert result.title == "Photosynthesis" and result.subject == "Biology"
    assert len(result.key_ideas) == 3
    assert len(result.lines) == 6


def test_generate_script_missing_model_message():
    client = _client(lambda request: httpx.Response(404, json={"error": "model not found"}))
    with pytest.raises(ScriptError, match="ollama pull"):
        generate_script("material", ASKER, EXPLAINER, get_settings(), client=client)

import json

import httpx
import pytest

from app.assets import Character
from app.config import get_settings
from app.pipeline.script import ScriptError, build_prompt, generate_script, parse_script

ASKER = Character(id="dex", name="Dex", role="asker", persona="curious", color="#3BC8FF")
EXPLAINER = Character(id="nova", name="Prof. Nova", role="explainer", persona="smug", color="#FFB23B")


def script_json(n: int = 6, **extra) -> str:
    lines = [{"speaker": "A" if i % 2 == 0 else "B", "text": f"Line number {i}."} for i in range(n)]
    return json.dumps({"title": "Plants Eat Light", "lines": lines, **extra})


def test_parse_script_maps_speakers():
    result = parse_script(script_json(), ASKER, EXPLAINER)
    assert result.title == "Plants Eat Light"
    assert [line.character_id for line in result.lines[:2]] == ["dex", "nova"]
    assert len(result.lines) == 6


def test_parse_script_recovers_json_wrapped_in_prose():
    raw = "Sure! Here you go:\n```json\n" + script_json() + "\n```"
    assert len(parse_script(raw, ASKER, EXPLAINER).lines) == 6


def test_parse_script_cleans_text():
    raw = json.dumps(
        {
            "lines": [
                {"speaker": "Dex", "text": 'Dex: "Wait, plants eat light?" (gasps)'},
                {"speaker": "nova", "text": "B: *sighs* Yes,   basically."},
                {"speaker": "???", "text": "Unknown speakers alternate."},
                {"speaker": "A", "text": "   "},
                {"speaker": "B", "text": "Ok."},
            ]
        }
    )
    lines = parse_script(raw, ASKER, EXPLAINER).lines
    assert lines[0].text == "Wait, plants eat light?"
    assert lines[1].text == "Yes, basically."
    assert lines[2].character_id == "dex"  # previous was the explainer
    assert len(lines) == 4  # empty line dropped


def test_parse_script_rejects_too_few_lines():
    with pytest.raises(ScriptError, match="usable lines"):
        parse_script(script_json(2), ASKER, EXPLAINER)


def test_parse_script_rejects_non_json():
    with pytest.raises(ScriptError):
        parse_script("no json here", ASKER, EXPLAINER)


def test_build_prompt_truncates_long_material():
    prompt = build_prompt("Sentence. " * 5000, ASKER, EXPLAINER)
    assert "Dex" in prompt and "Prof. Nova" in prompt
    assert len(prompt) < 12000


def _client(handler) -> httpx.Client:
    return httpx.Client(base_url="http://ollama.test", transport=httpx.MockTransport(handler))


def test_generate_script_retries_then_succeeds():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content))
        content = "garbage" if len(calls) == 1 else script_json()
        return httpx.Response(200, json={"message": {"content": content}})

    result = generate_script("material", ASKER, EXPLAINER, get_settings(), client=_client(handler))
    assert len(calls) == 2
    assert calls[0]["format"]["type"] == "object"
    assert len(result.lines) == 6


def test_generate_script_missing_model_message():
    client = _client(lambda request: httpx.Response(404, json={"error": "model not found"}))
    with pytest.raises(ScriptError, match="ollama pull"):
        generate_script("material", ASKER, EXPLAINER, get_settings(), client=client)

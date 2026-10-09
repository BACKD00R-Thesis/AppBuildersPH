"""Script generation with a local Ollama model, in two calls.

1. Key ideas: title, subject and the N most important ideas (N depends on video length).
2. Dialogue: the two characters teach those ideas, in English or Taglish.

Small models do better with one focused job per call, and the key ideas double
as the "What this video covers" list on the player.
"""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from string import Template

import httpx

from app.assets import Character
from app.config import Settings

PROMPTS = Path(__file__).parent / "prompts"
IDEAS_PROMPT = Template((PROMPTS / "ideas.txt").read_text(encoding="utf-8"))
DIALOGUE_PROMPT = Template((PROMPTS / "dialogue.txt").read_text(encoding="utf-8"))

# Small models have small context windows; keep the source to roughly 2k tokens.
MAX_SOURCE_CHARS = 8000
MAX_WORDS_PER_LINE = 40
ATTEMPTS = 2
SPEECH_WPS = 2.75  # matches the TTS pace in tts.py


@dataclass(frozen=True)
class LengthPlan:
    key_ideas: int
    min_lines: int
    max_lines: int


# Video length (seconds) -> how much to cover. The app shows "60s covers about 5 key ideas".
LENGTH_PLANS = {
    30: LengthPlan(key_ideas=3, min_lines=5, max_lines=8),
    60: LengthPlan(key_ideas=5, min_lines=8, max_lines=14),
    90: LengthPlan(key_ideas=8, min_lines=12, max_lines=20),
}

LANGUAGE = {
    True: (
        "Write in light Taglish: every explanation is in clear English. Add Filipino only as short "
        "reactions or fillers, at most one or two per line, like 'Grabe!', 'Ay naku,', 'diba?', "
        "'Ano ba', 'Sige', 'talaga?'. Example: A: \"Ay naku, so what does ATP even do?\" "
        'B: "It\'s the coins your cells spend, Tito. No ATP, no work, diba?"'
    ),
    False: "Write in English only.",
}

IDEAS_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "subject": {"type": "string"},
        "key_ideas": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "subject", "key_ideas"],
}

DIALOGUE_SCHEMA = {
    "type": "object",
    "properties": {
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "speaker": {"type": "string", "enum": ["A", "B"]},
                    "text": {"type": "string"},
                },
                "required": ["speaker", "text"],
            },
        },
    },
    "required": ["lines"],
}


class ScriptError(RuntimeError):
    pass


@dataclass(frozen=True)
class ScriptOptions:
    length_s: int = 60
    taglish: bool = True

    @property
    def plan(self) -> LengthPlan:
        return LENGTH_PLANS.get(self.length_s, LENGTH_PLANS[60])


@dataclass
class ScriptLine:
    character_id: str
    text: str


@dataclass
class Ideas:
    title: str | None
    subject: str | None
    key_ideas: list[str] = field(default_factory=list)


@dataclass
class Script:
    title: str | None
    subject: str | None
    key_ideas: list[str]
    lines: list[ScriptLine]


def trim_material(material: str) -> str:
    if len(material) <= MAX_SOURCE_CHARS:
        return material
    # Cut at a sentence boundary where possible.
    cut = material[:MAX_SOURCE_CHARS]
    return cut[: cut.rfind(". ") + 1] or cut


def build_ideas_prompt(material: str, options: ScriptOptions) -> str:
    return IDEAS_PROMPT.substitute(idea_count=options.plan.key_ideas, material=trim_material(material))


def build_prompt(
    material: str,
    asker: Character,
    explainer: Character,
    key_ideas: list[str] | None = None,
    options: ScriptOptions | None = None,
) -> str:
    options = options or ScriptOptions()
    plan = options.plan
    ideas = key_ideas or ["The most important ideas in the material"]
    return DIALOGUE_PROMPT.substitute(
        asker_name=asker.name,
        asker_persona=asker.persona,
        explainer_name=explainer.name,
        explainer_persona=explainer.persona,
        key_ideas="\n".join(f"{i}. {idea}" for i, idea in enumerate(ideas, 1)),
        min_lines=plan.min_lines,
        max_lines=plan.max_lines,
        target_seconds=options.length_s,
        target_words=round(options.length_s * SPEECH_WPS),
        language=LANGUAGE[options.taglish],
        material=trim_material(material),
    )


def _load_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Models sometimes wrap JSON in prose or code fences; take the outermost object.
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            raise ScriptError("The model didn't return JSON") from None
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ScriptError("The model returned malformed JSON") from exc


def _short_text(value: object, limit: int) -> str | None:
    text = re.sub(r"\s+", " ", str(value or "")).strip().strip("\"'“”.").strip()
    return text[:limit] or None


def parse_ideas(raw: str, options: ScriptOptions | None = None) -> Ideas:
    options = options or ScriptOptions()
    data = _load_json(raw)
    if not isinstance(data, dict):
        raise ScriptError("The model's JSON wasn't an object")
    ideas = []
    for item in data.get("key_ideas") or []:
        text = _short_text(item, 80)
        if text and text.lower() not in {i.lower() for i in ideas}:
            ideas.append(text[0].upper() + text[1:])
    if not ideas:
        raise ScriptError("The model found no key ideas")
    return Ideas(
        title=_short_text(data.get("title"), 80),
        subject=_short_text(data.get("subject"), 40),
        key_ideas=ideas[: options.plan.key_ideas],
    )


def _clean_line(text: str, names: list[str]) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    # Strip "Name:" / "A:" prefixes and wrapping quotes.
    prefix = "|".join(re.escape(n) for n in [*names, "A", "B"])
    text = re.sub(rf"^(?:{prefix})\s*:\s*", "", text, flags=re.I)
    # Drop stage directions like (laughs) or *sighs*.
    text = re.sub(r"\([^)]*\)|\*[^*]*\*|\[[^\]]*\]", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip().strip("\"'“”").strip()
    words = text.split()
    if len(words) > MAX_WORDS_PER_LINE:
        text = " ".join(words[:MAX_WORDS_PER_LINE]).rstrip(",;:") + "…"
    return text


def fix_self_address(text: str, own_name: str, other_name: str) -> str:
    """Small models flip who calls whom ("Tito Boy, how..." said by Tito Boy). Address the other one."""
    own = re.escape(own_name)
    text = re.sub(rf"^{own}(?=\s*[,!])", other_name, text, flags=re.I)
    return re.sub(rf"(,\s*){own}(?=\s*[.!?,]|$)", rf"\g<1>{other_name}", text, flags=re.I)


def parse_lines(
    raw: str, asker: Character, explainer: Character, options: ScriptOptions | None = None
) -> list[ScriptLine]:
    options = options or ScriptOptions()
    data = _load_json(raw)
    items = data.get("lines") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise ScriptError("The model's JSON had no 'lines' list")

    by_speaker = {
        "a": asker.id,
        asker.id.lower(): asker.id,
        asker.name.lower(): asker.id,
        "b": explainer.id,
        explainer.id.lower(): explainer.id,
        explainer.name.lower(): explainer.id,
    }
    names = [asker.name, explainer.name]
    lines: list[ScriptLine] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        speaker = str(item.get("speaker", "")).strip().lower()
        text = _clean_line(item.get("text", ""), names)
        if not text:
            continue
        # Unknown speaker: alternate from the previous line.
        if speaker in by_speaker:
            character_id = by_speaker[speaker]
        elif lines and lines[-1].character_id == asker.id:
            character_id = explainer.id
        else:
            character_id = asker.id
        if character_id == asker.id:
            text = fix_self_address(text, asker.name, explainer.name)
        else:
            text = fix_self_address(text, explainer.name, asker.name)
        lines.append(ScriptLine(character_id=character_id, text=text))

    if len(lines) < 4:
        raise ScriptError(f"The model only wrote {len(lines)} usable lines")
    return lines[: options.plan.max_lines + 4]


def check_lines(lines: list[ScriptLine]) -> list[ScriptLine]:
    """Drop repeated lines: small models sometimes loop on a sentence."""
    seen: set[str] = set()
    result: list[ScriptLine] = []
    for line in lines:
        key = re.sub(r"\W+", " ", line.text.lower()).strip()
        if key not in seen:
            seen.add(key)
            result.append(line)
    if len(result) < 4:
        raise ScriptError(f"Only {len(result)} distinct lines were left after checking the script")
    return result


def _chat(
    client: httpx.Client, settings: Settings, prompt: str, schema: dict, parse: Callable[[str], object]
):
    payload = {
        "model": settings.ollama_model,
        "messages": [{"role": "user", "content": prompt}],
        "format": schema,
        "stream": False,
        "options": {"temperature": 0.8, "num_ctx": 8192},
    }
    last_error: Exception | None = None
    for _ in range(ATTEMPTS):
        try:
            response = client.post("/api/chat", json=payload)
        except httpx.HTTPError as exc:
            raise ScriptError(
                f"Couldn't reach Ollama at {settings.ollama_host}. Is `ollama serve` running?"
            ) from exc
        if response.status_code == 404:
            raise ScriptError(
                f"Ollama doesn't have the model '{settings.ollama_model}'. "
                f"Run: ollama pull {settings.ollama_model}"
            )
        if response.status_code >= 400:
            raise ScriptError(f"Ollama error {response.status_code}: {response.text[:200]}")
        content = response.json().get("message", {}).get("content", "")
        try:
            return parse(content)
        except ScriptError as exc:
            last_error = exc
    raise ScriptError(f"Script generation failed after {ATTEMPTS} attempts: {last_error}")


def generate_script(
    material: str,
    asker: Character,
    explainer: Character,
    settings: Settings,
    options: ScriptOptions | None = None,
    client: httpx.Client | None = None,
    on_step: Callable[[str], None] | None = None,
) -> Script:
    """Key ideas, then the dialogue. `on_step` gets "ideas", "jokes" and "check" as work starts."""
    options = options or ScriptOptions()
    step = on_step or (lambda _: None)
    own_client = client is None
    client = client or httpx.Client(base_url=settings.ollama_host, timeout=settings.ollama_timeout_s)
    try:
        step("ideas")
        ideas: Ideas = _chat(
            client,
            settings,
            build_ideas_prompt(material, options),
            IDEAS_SCHEMA,
            lambda raw: parse_ideas(raw, options),
        )
        step("jokes")
        lines: list[ScriptLine] = _chat(
            client,
            settings,
            build_prompt(material, asker, explainer, ideas.key_ideas, options),
            DIALOGUE_SCHEMA,
            lambda raw: parse_lines(raw, asker, explainer, options),
        )
        step("check")
        lines = check_lines(lines)
        return Script(title=ideas.title, subject=ideas.subject, key_ideas=ideas.key_ideas, lines=lines)
    finally:
        if own_client:
            client.close()


def ollama_status(settings: Settings) -> dict:
    try:
        response = httpx.get(f"{settings.ollama_host}/api/tags", timeout=3)
        response.raise_for_status()
    except httpx.HTTPError:
        return {"ok": False, "detail": f"Ollama not reachable at {settings.ollama_host}"}
    models = {m.get("name", "") for m in response.json().get("models", [])}
    wanted = settings.ollama_model
    has_model = wanted in models or f"{wanted}:latest" in models
    return {
        "ok": has_model,
        "detail": wanted if has_model else f"Model missing. Run: ollama pull {wanted}",
    }

"""Dialogue generation with a local Ollama model."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from string import Template

import httpx

from app.assets import Character
from app.config import Settings

PROMPT = Template((Path(__file__).parent / "prompts" / "dialogue.txt").read_text(encoding="utf-8"))

# Small models have small context windows; keep the source to roughly 2k tokens.
MAX_SOURCE_CHARS = 8000
MIN_LINES, MAX_LINES = 8, 16
MAX_WORDS_PER_LINE = 40
ATTEMPTS = 2

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
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


@dataclass
class ScriptLine:
    character_id: str
    text: str


@dataclass
class Script:
    title: str | None
    lines: list[ScriptLine]


def build_prompt(material: str, asker: Character, explainer: Character) -> str:
    if len(material) > MAX_SOURCE_CHARS:
        # Cut at a sentence boundary where possible.
        cut = material[:MAX_SOURCE_CHARS]
        material = cut[: cut.rfind(". ") + 1] or cut
    return PROMPT.substitute(
        asker_name=asker.name,
        asker_persona=asker.persona,
        explainer_name=explainer.name,
        explainer_persona=explainer.persona,
        min_lines=MIN_LINES,
        max_lines=MAX_LINES,
        target_seconds=60,
        material=material,
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


def parse_script(raw: str, asker: Character, explainer: Character) -> Script:
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
        lines.append(ScriptLine(character_id=character_id, text=text))

    if len(lines) < 4:
        raise ScriptError(f"The model only wrote {len(lines)} usable lines")
    title = data.get("title")
    title = str(title).strip()[:80] if title else None
    return Script(title=title or None, lines=lines[: MAX_LINES + 4])


def generate_script(
    material: str,
    asker: Character,
    explainer: Character,
    settings: Settings,
    client: httpx.Client | None = None,
) -> Script:
    prompt = build_prompt(material, asker, explainer)
    payload = {
        "model": settings.ollama_model,
        "messages": [{"role": "user", "content": prompt}],
        "format": RESPONSE_SCHEMA,
        "stream": False,
        "options": {"temperature": 0.8, "num_ctx": 8192},
    }
    own_client = client is None
    client = client or httpx.Client(base_url=settings.ollama_host, timeout=settings.ollama_timeout_s)
    last_error: Exception | None = None
    try:
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
                return parse_script(content, asker, explainer)
            except ScriptError as exc:
                last_error = exc
        raise ScriptError(f"Script generation failed after {ATTEMPTS} attempts: {last_error}")
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

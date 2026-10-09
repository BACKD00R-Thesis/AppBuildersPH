"""Pre-download the TTS and Whisper models so the server works fully offline.

Synthesizes one short line per character and aligns it, which makes each engine
fetch its weights. Ollama models are pulled separately: `ollama pull <model>`.
"""

import tempfile
from pathlib import Path

from app.assets import load_characters
from app.config import get_settings
from app.pipeline import align, tts


def main() -> None:
    settings = get_settings()
    print(f"TTS engine: {settings.tts_engine}")
    with tempfile.TemporaryDirectory() as tmp:
        for character in load_characters(settings):
            path = Path(tmp) / f"{character.id}.wav"
            print(f"  voice for {character.name}: {tts.voice_for(character, settings)}")
            tts.synthesize("Testing, one two three.", character, path, settings)
        if align.whisper_available():
            print(f"Whisper model: {settings.whisper_model}")
            align.align(path, "Testing, one two three.", settings)
        else:
            print("faster-whisper not installed; skipping (captions will use estimated timing)")
    print(f"Done. Remember: ollama pull {settings.ollama_model}")


if __name__ == "__main__":
    main()

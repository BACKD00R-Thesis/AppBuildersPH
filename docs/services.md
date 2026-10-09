# Services

The services Brainrot Study depends on, what each is for, and how it's configured.

**Brainrot Study uses no cloud services at runtime.** No Vercel, no Supabase, no OpenAI, no ElevenLabs. Every service below runs on the user's machine or local network. The only internet access needed is the one-time download of tools and models.

Before adding any hosted service, write a decision record in [decisions/](decisions/); it would change the product's core promise.

## Runtime services

### Ollama: local LLM

| | |
|---|---|
| **Purpose** | Reads the extracted PDF text and writes the two-character ELI5 dialogue as JSON |
| **Models** | `llama3.2:3b` (default), `qwen2.5:3b` (lighter, good at structured JSON) |
| **How we call it** | HTTP API, `POST /api/chat` with `format: "json"` |
| **Install** | https://ollama.com, then `ollama pull <model>` |
| **Env vars** | `OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT_S` |

### Kokoro-TTS: primary text-to-speech

| | |
|---|---|
| **Purpose** | Natural-sounding voices for each character's lines and for previews |
| **How we call it** | Python package, in-process |
| **Notes** | Small (around 82M parameters), fast on CPU, multiple voices |
| **Env vars** | `TTS_ENGINE=kokoro`, `KOKORO_VOICE_A`, `KOKORO_VOICE_B`, `MODELS_DIR` |

### Piper TTS: fallback text-to-speech

| | |
|---|---|
| **Purpose** | Lighter, faster TTS for low-spec machines |
| **How we call it** | Python package or CLI, one ONNX voice model per character |
| **Env vars** | `TTS_ENGINE=piper`, `PIPER_VOICE_A`, `PIPER_VOICE_B`, `MODELS_DIR` |

### Dummy TTS: development only

| | |
|---|---|
| **Purpose** | A soft beep per word at a speech-like pace, so the full pipeline (previews, captions, renders) works before any model is downloaded |
| **Env vars** | `TTS_ENGINE=dummy` |

### faster-whisper: word-level timestamps

| | |
|---|---|
| **Purpose** | Transcribes each synthesized line to get the start and end time of every word, used to time the captions. Optional: without it, word timing is estimated from word length |
| **How we call it** | Python package, in-process, `word_timestamps=True` |
| **Models** | `base` (fast), `small` (default, more accurate) |
| **Env vars** | `WHISPER_MODEL`, `WHISPER_DEVICE` (`cpu` or `cuda`), `WHISPER_COMPUTE_TYPE` (`int8`, `float16`) |

### FFmpeg: video composition

| | |
|---|---|
| **Purpose** | Loops and crops the background clip, overlays characters, mixes audio, burns in ASS captions, encodes the MP4 |
| **How we call it** | Subprocess |
| **Install** | https://ffmpeg.org/download.html (must include `libass` and `libx264`) |
| **Env vars** | `FFMPEG_PATH` |

### SQLite: local database

| | |
|---|---|
| **Purpose** | Projects, scripts, lines, and render jobs |
| **How we call it** | SQLModel / SQLAlchemy |
| **Env vars** | `DATABASE_URL` |

## Libraries with no configuration

| Library | Purpose |
|---|---|
| PyMuPDF | Extracts text from uploaded PDFs |
| FastAPI | The API, and serves the built web app. Its OpenTelemetry hooks (added in 0.143) are switched off in `app/main.py` |
| React, React Router, Tailwind CSS 4, Vite | The web app (`apps/web`) |
| `@fontsource/*` | Bundled fonts (Playfair Display, Plus Jakarta Sans, Archivo Black) so the app needs no font CDN |

The app uses only standard browser features: `fetch`, `<audio>`, `<video>`, file inputs, downloads, and the Web Share API (on phones that support sharing files).

## Development-only services

| Service | Purpose | Notes |
|---|---|---|
| GitHub | Source hosting, issues, PRs, Actions CI | CI runs lint and tests only; it never needs model weights |
| npm registry | Installing the web app's dependencies | Only at install time; the built app runs offline |
| Figma | UI design | Link in [design.md](design.md) |

## Adding a service

1. Confirm it runs fully locally (or write a decision record explaining why it can't).
2. Add a section here: purpose, how we call it, install link, env vars.
3. Add its variables to [.env.example](../.env.example) and [development.md](development.md).
4. Add it to the `/api/health` check (the laptop sidebar's engine card reads it).

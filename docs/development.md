# Development

Everything you need to run Brainrot Study locally and make changes. If a step here is wrong or missing, fix this doc in the same PR.

## Prerequisites

| Tool | Version | Why |
|---|---|---|
| Node.js | 20.19+ or 22.12+ | Web app (Vite 8) |
| Python | 3.11 or 3.12 | The engine (FastAPI). Core works on newer versions, but the AI engines (PyTorch, CTranslate2) publish wheels for new Pythons late |
| Ollama | latest | Local LLM |
| FFmpeg | 6 or newer, built with `libass` and `libx264`, on `PATH` | Video rendering |
| Git | any recent | Source control |

Optional: an NVIDIA GPU with CUDA speeds up faster-whisper and TTS. Everything works on CPU.

Hardware we test on: a laptop with 16 GB RAM. 8 GB works with `qwen2.5:3b` and the `base` Whisper model, but rendering is slower.

On Windows, `winget install Gyan.FFmpeg` and `winget install Ollama.Ollama` install the two binaries. Open a new terminal afterwards so `PATH` updates.

## How the pieces fit

One process, the **engine** (`server/`), does everything at runtime: the REST API under `/api`, the AI pipeline, and serving the built **web app** (`apps/web/dist`) at `/`. Laptops and phones on the same Wi-Fi open `http://<laptop-ip>:8000`.

While working on the UI, run the Vite dev server instead (hot reload); it proxies `/api` to the engine.

## First-time setup

```bash
git clone <your-fork-url>
cd <repo>
cp .env.example .env
```

Every variable has a working default, so you only need to fill in what differs on your machine (see [Environment variables](#environment-variables)). Blank values mean "use the default". Set `USER_NAME` to see "Kumusta, <name>!".

### 1. Engine

```bash
cd server
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt            # API + pipeline (light)
pip install -r requirements-engines.txt    # Kokoro, Piper, faster-whisper (heavy, downloads PyTorch)
pip install -r requirements-expressive.txt # optional: Expressive voices (NVIDIA GPU, ~8 GB with CUDA PyTorch)
python -m app.scripts.init_db
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000/api/health`. It reports whether Ollama, TTS, Whisper, and FFmpeg are ready. Interactive API docs are at `http://localhost:8000/api/docs`.

**No models yet?** Set `TTS_ENGINE=dummy` in `.env`. Voices become soft beeps at the real speaking pace so you can build and test the whole flow, including rendering, before downloading anything. Without faster-whisper installed, captions use estimated word timing.

### 2. Models

```bash
ollama pull llama3.2:3b        # or: ollama pull qwen2.5:3b, then set OLLAMA_MODEL
python -m app.scripts.download_models   # from server/, pre-fetches TTS and Whisper weights for offline use
```

For Piper instead of Kokoro, download the two voice models named in [assets/characters/manifest.json](../assets/characters/manifest.json) (`en_US-ryan-medium` and `en_US-amy-medium`, each an `.onnx` plus `.onnx.json`) into `models/piper/`, and set `TTS_ENGINE=piper`.

### 3. Web app

To use it (served by the engine):

```bash
cd apps/web
npm install
npm run build        # writes apps/web/dist; restart the engine the first time so it picks it up
```

Then open `http://localhost:8000`. On a phone, find the laptop's address with `ipconfig` (Windows) or `ipconfig getifaddr en0` (macOS) and open `http://<that-ip>:8000`.

To work on it (hot reload):

```bash
cd apps/web
npm run dev          # http://localhost:5173, also on your Wi-Fi address; /api goes to the engine
```

Read [apps/web/HANDOFF.md](../apps/web/HANDOFF.md) before changing screens: it maps every route to its Figma frame and lists the design rules. Open `/_screens` for a list of every screen.

### 4. Background clips and fonts

Each background in [assets/backgrounds/manifest.json](../assets/backgrounds/manifest.json) has a gradient (what the app previews). With no clip file, renders use that gradient. To use gameplay footage, put the MP4 named in the manifest in `assets/backgrounds/` (ideally 1080x1920 or larger and at least 60 seconds long):

```json
{ "id": "parkour", "name": "Parkour run", "short_name": "Parkour", "gradient": ["#3b4a2e", "#151a14"], "file": "parkour.mp4", "duration_s": 300 }
```

`duration_s` lets each render start at a random point in the clip. Clips are git-ignored: only use footage you recorded or are licensed to use.

Burned-in captions use **Archivo Black** (Bold pop, Outline) and **Plus Jakarta Sans** (Clean), the same fonts as the app. Drop `ArchivoBlack-Regular.ttf` and `PlusJakartaSans-Bold.ttf` (both SIL Open Font License) into `assets/fonts/`; without them FFmpeg falls back to a system font.

## Environment variables

[.env.example](../.env.example) lists every variable. Summary:

| Variable | Default | Purpose |
|---|---|---|
| `API_HOST`, `API_PORT` | `0.0.0.0`, `8000` | Where `python -m app` listens (plain `uvicorn` uses its own flags) |
| `API_PAIRING_TOKEN` | empty (off) | Shared secret. When set, open the app once as `/?token=<token>` on each device |
| `API_CORS_ORIGINS` | empty | Comma-separated origins, only if the app is served from another origin |
| `USER_NAME` | empty | Name in the greeting |
| `DATA_DIR` | `./data` | Uploaded PDFs and notes, audio, captions, renders, and the database |
| `MODELS_DIR` | `./models` | Downloaded TTS and Whisper models |
| `DATABASE_URL` | `sqlite:///<DATA_DIR>/brainrot.db` | SQLite connection string |
| `WEB_DIST_DIR` | `./apps/web/dist` | Built web app served at `/` |
| `OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT_S` | `http://127.0.0.1:11434`, `llama3.2:3b`, `180` | LLM endpoint and model |
| `TTS_ENGINE` | `kokoro` | `kokoro`, `piper`, or `dummy` |
| `KOKORO_VOICE_A/B`, `PIPER_VOICE_A/B` | from the character manifest | Override the asker (A, Bunso) and explainer (B, Tito) voices |
| `EXPRESSIVE_DEVICE` | `cuda` | Where the optional Expressive voices (Chatterbox) run; `cpu` works but is very slow. Without `requirements-expressive.txt` or a CUDA GPU the app greys the option out |
| `WHISPER_MODEL`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE` | `small`, `cpu`, `int8` | Alignment model and hardware |
| `FFMPEG_PATH` | `ffmpeg` | FFmpeg binary |
| `RENDER_WIDTH`, `RENDER_HEIGHT`, `RENDER_FPS` | `1080`, `1920`, `30` | Output video format |
| `ENGINE_URL` | `http://localhost:8000` | Where `npm run dev` proxies `/api` |

Never commit `.env`. Add new variables to `.env.example`, `server/app/config.py`, and this table in the same PR.

## Database

- SQLite at `DATABASE_URL`. Tables: `project`, `line`, `render` ([server/app/models.py](../server/app/models.py)).
- On startup (and `python -m app.scripts.init_db`), missing tables are created and **missing columns are added** with their defaults, so older databases keep working when the schema grows. `--reset` drops all data.
- Renaming or removing a column still needs a reset (or a real migration tool, once we add one); note it in your PR.
- Deleting `DATA_DIR` resets everything, including renders.

## Common commands

| Task | Command (run from) |
|---|---|
| Start the engine with reload | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` (`server/`) |
| Start the engine from `.env` settings | `python -m app` (`server/`) |
| Engine tests | `pytest` (`server/`); render tests are skipped if FFmpeg isn't on `PATH` |
| Engine lint and format | `ruff check . && ruff format .` (`server/`) |
| Web app dev server | `npm run dev` (`apps/web/`) |
| Web app type check + build | `npm run build` (`apps/web/`) |
| Print a script for a PDF | `python -m app.scripts.script_sample file.pdf --pages 1-5` (`server/`) |
| Render a video from the CLI | `python -m app.scripts.render_sample file.pdf` or `--script lines.txt` to skip the LLM (`server/`) |
| Re-render the mascot PNGs after a design change | `python -m app.scripts.render_mascots` (`server/`, needs Edge or Chrome) |

## Common workflows

### Change the prompts

1. Edit [ideas.txt](../server/app/pipeline/prompts/ideas.txt) (key ideas, title, subject) or [dialogue.txt](../server/app/pipeline/prompts/dialogue.txt) (the script). Placeholders use `$name` syntax. Taglish wording lives in `LANGUAGE` in [script.py](../server/app/pipeline/script.py).
   Taglish mode is parked: new videos default to English and the toggle is hidden while `TAGLISH_ENABLED` in [options.ts](../apps/web/src/lib/options.ts) is `false`, because the TTS engines have no Tagalog voice. Set it to `true` to bring the toggle back.
2. Run `python -m app.scripts.script_sample path/to/file.pdf` to print the generated script without rendering.
3. Check it against two or three different PDFs, in English and Taglish, before opening a PR.

### Add or change a character

1. Add a transparent PNG (around 512x512) to `assets/characters/`.
2. Add an entry to `assets/characters/manifest.json`: `id`, `name`, `role` (`asker` or `explainer`), `vibe`, `persona` (goes into the prompt), `color`, `sample` (the "Hear sample" line), `voices` (per engine), and `image`.
3. Restart the engine. The app's avatars and labels for `tito-boy` and `bunso` are in [apps/web/src/lib/speakers.ts](../apps/web/src/lib/speakers.ts); other ids get a plain fallback.

### Debug a failed render

1. The app shows the error; `GET /api/renders/{id}` has the failed step and message.
2. Intermediate files are in `DATA_DIR/projects/{project_id}/`: per-line WAVs and word timings in `audio/`, and `captions.ass`, `voice.wav`, and `render.log` (every FFmpeg command and its output) in `renders/{render_id}/`.
3. Re-run the logged FFmpeg command from that folder to see the full output.

## Troubleshooting

- **Phone can't open the app:** use the laptop's LAN IP, start the engine with `--host 0.0.0.0`, and allow port 8000 in the firewall. On Windows, a Wi-Fi network set to *Public* blocks it; set it to *Private*.
- **The laptop shows the old UI:** run `npm run build` in `apps/web` again; the engine serves whatever is in `dist`.
- **`/` returns 404:** the web app hasn't been built yet, or the engine started before `dist` existed. Build it and restart the engine.
- **Script generation fails:** run `ollama list` to confirm the model is pulled and that Ollama is running. The sidebar's engine card and `/api/health` show the exact problem.
- **"Kokoro isn't installed":** run `pip install -r requirements-engines.txt`, or set `TTS_ENGINE=dummy` while developing.
- **FFmpeg not found:** set `FFMPEG_PATH` to the full path of the binary.
- **Out of memory during render:** switch to `qwen2.5:3b`, use `WHISPER_MODEL=base`, and close other apps.

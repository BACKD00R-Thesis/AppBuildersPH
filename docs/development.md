# Development

Everything you need to run Brainrot Study locally and make changes. If a step here is wrong or missing, fix this doc in the same PR.

## Prerequisites

| Tool | Version | Why |
|---|---|---|
| Node.js | 20 LTS or newer | Expo app |
| Python | 3.11 or newer | FastAPI backend |
| Ollama | latest | Local LLM |
| FFmpeg | 6 or newer, on `PATH` | Video rendering |
| Git | any recent | Source control |
| Expo Go app | latest | Running the app on your phone |

Optional: an NVIDIA GPU with CUDA speeds up faster-whisper and TTS. Everything works on CPU.

Hardware we test on: a laptop with 16 GB RAM. 8 GB works with `qwen2.5:3b` and the `base` Whisper model, but rendering is slower.

## First-time setup

```bash
git clone <your-fork-url>
cd <repo>
cp .env.example .env
```

Edit `.env` for your machine (see [Environment variables](#environment-variables)).

### 1. Models

```bash
ollama pull llama3.2:3b        # or: ollama pull qwen2.5:3b
```

TTS and Whisper models download on first use into `MODELS_DIR`. To pre-download them (for example, before going offline):

```bash
cd server
python -m app.scripts.download_models
```

### 2. Backend

```bash
cd server
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.scripts.init_db      # creates the SQLite database
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Check it's running: open `http://localhost:8000/health`. It reports whether Ollama, TTS, Whisper, and FFmpeg are reachable.

### 3. Mobile app

```bash
cd apps/mobile
npm install
npx expo start
```

Scan the QR code with Expo Go. Your phone and laptop must be on the same Wi-Fi or hotspot.

Set `EXPO_PUBLIC_API_URL` to your laptop's LAN address (for example `http://192.168.1.23:8000`), not `localhost`, because `localhost` on the phone means the phone itself.

### 4. Background clips

Gameplay clips are not committed (size and licensing). Put MP4 files in `assets/backgrounds/`, ideally 1080x1920 or larger and at least 60 seconds long. Add an entry for each in `assets/backgrounds/manifest.json`:

```json
[{ "id": "parkour-01", "name": "Parkour", "file": "parkour-01.mp4" }]
```

## Environment variables

[.env.example](../.env.example) lists every variable. Summary:

| Variable | Used by | Purpose |
|---|---|---|
| `API_HOST`, `API_PORT` | Backend | Where FastAPI listens |
| `API_PAIRING_TOKEN` | Backend + app | Shared token so other devices on the LAN can't use your API |
| `DATA_DIR` | Backend | Uploaded PDFs, audio, renders |
| `MODELS_DIR` | Backend | Downloaded TTS and Whisper models |
| `DATABASE_URL` | Backend | SQLite connection string |
| `OLLAMA_HOST`, `OLLAMA_MODEL` | Backend | LLM endpoint and model |
| `TTS_ENGINE`, `KOKORO_*`, `PIPER_*` | Backend | Which TTS engine and voices to use |
| `WHISPER_MODEL`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE` | Backend | Alignment model and hardware |
| `FFMPEG_PATH` | Backend | FFmpeg binary |
| `EXPO_PUBLIC_API_URL` | App | Backend base URL, as seen from the phone |
| `EXPO_PUBLIC_API_PAIRING_TOKEN` | App | Same value as `API_PAIRING_TOKEN` |

Never commit `.env`. Add new variables to `.env.example` and this table in the same PR.

## Database

- SQLite at the path in `DATABASE_URL` (default `./data/brainrot.db`).
- Create or reset it: `python -m app.scripts.init_db` (add `--reset` to drop all data).
- Schema changes go through Alembic: `alembic revision --autogenerate -m "describe change"` then `alembic upgrade head`.
- Deleting `DATA_DIR` resets everything, including renders.

## Common commands

| Task | Command (run from) |
|---|---|
| Start backend with reload | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` (`server/`) |
| Backend tests | `pytest` (`server/`) |
| Backend lint and format | `ruff check . && ruff format .` (`server/`) |
| Start the app | `npx expo start` (`apps/mobile/`) |
| App lint | `npm run lint` (`apps/mobile/`) |
| App type check | `npm run typecheck` (`apps/mobile/`) |
| App tests | `npm test` (`apps/mobile/`) |
| Render a script from the CLI | `python -m app.scripts.render_sample path/to/file.pdf` (`server/`) |

## Common workflows

### Change the dialogue prompt

1. Edit the prompt template in `server/app/pipeline/prompts/`.
2. Run `python -m app.scripts.script_sample path/to/file.pdf` to print the generated script without rendering.
3. Check it against two or three sample PDFs in `server/tests/fixtures/` before opening a PR.

### Add a character

1. Add an image (transparent PNG, roughly 800 px tall) to `assets/characters/`.
2. Add an entry to `assets/characters/manifest.json` with name, persona prompt, TTS engine, and voice ID.
3. Restart the backend; the character appears in `GET /assets/characters`.

### Debug a failed render

1. Open `GET /renders/{id}` to see which step failed and the error.
2. Intermediate files are in `DATA_DIR/projects/{project_id}/`: per-line WAVs, `captions.ass`, and the FFmpeg command in `render.log`.
3. Re-run the logged FFmpeg command by hand to see the full output.

## Troubleshooting

- **App can't reach the backend:** check `EXPO_PUBLIC_API_URL` uses the LAN IP, the backend was started with `--host 0.0.0.0`, and your OS firewall allows port 8000.
- **Ollama errors:** run `ollama list` to confirm the model is pulled and `ollama serve` is running.
- **FFmpeg not found:** set `FFMPEG_PATH` to the full path of the binary.
- **Out of memory during render:** switch to `qwen2.5:3b`, use `WHISPER_MODEL=base`, and close other apps.

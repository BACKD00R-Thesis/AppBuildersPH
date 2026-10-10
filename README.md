# Brainrot Study

> Working title. An open-source, 100% local AI app that turns boring study PDFs into short "brainrot" educational videos: Bunso asks and Tito explains the material in a short, funny dialogue over gameplay footage.

Upload a lecture PDF (or paste your notes), let a local LLM rewrite it as an ELI5 conversation, tweak the script, pick a style, and export a 9:16 MP4 with word-by-word captions. Use it on your laptop, or on your phone over the same Wi-Fi. Nothing leaves your network: no OpenAI, no ElevenLabs, no cloud bills.

## Features

- **ELI5 dialogue engine**: finds the key ideas, then writes a back-and-forth between Bunso (asks) and Tito (explains). 30, 60 or 90 seconds, in English (Taglish is parked for now).
- **Editable script**: tap a line to rewrite it, add lines, regenerate.
- **Voice previews**: hear any line, or a sample of each voice, before rendering.
- **Brainrot captions**: up to two lines at a time, the spoken word highlighted in mustard, in Bold pop, Clean or Outline style.
- **Backgrounds**: parkour, kart race, block break or soap cut, as gameplay clips or matching gradients.
- **"What this video covers"**: the key ideas listed next to the finished video.
- **100% offline and private**: LLM, TTS, alignment and video rendering all run on your laptop.

## How it works

```
[ Upload PDF / notes ] ──> [ Edit AI script ] ──> [ Pick a style ] ──> [ Watch & share ]
```

## Tech stack

| Layer | Choice |
|---|---|
| App (laptop + phone) | React 19, Vite, Tailwind CSS 4, React Router, built from the Figma mockups |
| Engine API | FastAPI (Python); also serves the app |
| LLM | Ollama (`llama3.2:3b` or `qwen2.5:3b`) |
| Text-to-speech | Quick voices: Kokoro-TTS or Piper TTS. Optional Expressive voices: Chatterbox (NVIDIA GPU) |
| Word timestamps | faster-whisper |
| Video composition | FFmpeg CLI |

## Quickstart

You need Node.js 20.19+, Python 3.11 or 3.12, FFmpeg, and Ollama. Full steps are in [docs/development.md](docs/development.md).

```bash
cp .env.example .env            # blank values use sensible defaults; set USER_NAME for the greeting
ollama pull llama3.2:3b

# Build the app once
cd apps/web && npm install && npm run build && cd ../..

# Start the engine (serves the app too)
cd server
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-engines.txt
python -m app
```

Open `http://localhost:8000` on the laptop, or `http://<laptop-ip>:8000` on a phone on the same Wi-Fi. To try the flow before downloading voice models, set `TTS_ENGINE=dummy` in `.env`.

## Documentation

| Doc | What it covers |
|---|---|
| [docs/product.md](docs/product.md) | Problem, target users, features, user flows, requirements |
| [docs/architecture.md](docs/architecture.md) | System diagram, components, data flow, core entities |
| [docs/design.md](docs/design.md) | Figma, design tokens, typography, layouts, video style |
| [docs/development.md](docs/development.md) | Local setup, commands, env vars, database, common workflows |
| [docs/services.md](docs/services.md) | The local services the engine depends on and their config |
| [docs/decisions/](docs/decisions/) | Architecture decision records |
| [apps/web/HANDOFF.md](apps/web/HANDOFF.md) | Frontend notes: routes, components, what differs from Figma |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Branches, commits, PRs, reviews, merge rules |
| [.env.example](.env.example) | Every environment variable the project reads |

## Project layout

```
project-root/
├── apps/
│   └── web/                    # The app: laptop and phone layouts from Figma
│       ├── src/
│       │   ├── screens/        # desktop/ and mobile/ screens
│       │   ├── components/     # Button, VideoFrame, ScriptList, Steps, …
│       │   ├── layouts/        # DesktopShell (sidebar), MobileShell
│       │   └── lib/            # API client, store, per-video hook, audio
│       ├── design-reference/   # Figma renders of the mobile screens
│       └── HANDOFF.md
├── server/
│   ├── app/
│   │   ├── routes/             # REST endpoints (under /api)
│   │   ├── pipeline/           # extract → script → tts → align → captions → render
│   │   ├── scripts/            # CLI tools (init_db, render_sample, …)
│   │   ├── workflow.py         # Runs the pipeline steps for a job
│   │   └── main.py             # FastAPI entry point; serves apps/web/dist
│   ├── tests/
│   ├── requirements.txt        # Core
│   └── requirements-engines.txt  # Kokoro, Piper, faster-whisper
├── assets/
│   ├── backgrounds/            # Gameplay clips + manifest with gradient colors (clips not committed)
│   └── characters/             # Tito and Bunso mascots (design files, one PNG per expression) + manifest
├── docs/
│   ├── product.md
│   ├── architecture.md
│   ├── design.md
│   ├── development.md
│   ├── services.md
│   └── decisions/
├── .env.example
├── CONTRIBUTING.md
└── README.md
```

## License

Open source. License to be chosen before the first public release (MIT is the current default).

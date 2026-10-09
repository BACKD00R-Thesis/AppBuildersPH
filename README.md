# Brainrot Study

> Working title. An open-source, 100% local AI mobile app that turns boring study PDFs into short "brainrot" educational videos: two characters explain the material in a comedic dialogue over gameplay footage.

Upload a lecture PDF, let a local LLM rewrite it as an ELI5 conversation, tweak the script, pick a background, and export a 9:16 MP4 with word-by-word captions. Nothing leaves your device or local network: no OpenAI, no ElevenLabs, no cloud bills.

## Features

- **ELI5 dialogue engine**: turns dense jargon into a back-and-forth between two personas (one asks simple questions, the other explains).
- **Editable script**: review, rewrite, reorder, or delete lines before rendering.
- **Voice previews**: tap any line to hear it in the character's voice before the full render.
- **Brainrot captions**: high-impact, word-by-word highlighted captions timed to the speech.
- **Background gameplay**: choose a looping clip (parkour, endless runner, etc.) for the bottom of the frame.
- **100% offline and private**: LLM, TTS, alignment, and video rendering all run locally.

## How it works

```
[ Upload PDF ] ──> [ Edit AI script ] ──> [ Customize style ] ──> [ Export & watch ]
```

1. **Upload**: import a lecture slide deck, paper, or textbook chapter.
2. **Script generation**: the local LLM extracts core concepts and writes a dialogue.
3. **Customize and preview**: edit lines, preview voices, choose background footage.
4. **Render and export**: the local engine synthesizes audio, aligns captions, and renders a vertical MP4.

## Tech stack

| Layer | Choice |
|---|---|
| Mobile app | React Native (Expo) + NativeWind |
| Local API | FastAPI (Python) |
| LLM | Ollama (`llama3.2:3b` or `qwen2.5:3b`) |
| Text-to-speech | Kokoro-TTS or Piper TTS |
| Word timestamps | faster-whisper |
| Video composition | FFmpeg CLI |

## Quickstart

You need Node.js 20+, Python 3.11+, FFmpeg, and Ollama installed. Full steps are in [docs/development.md](docs/development.md).

```bash
cp .env.example .env            # fill in values for your machine
ollama pull llama3.2:3b

# Local API
cd server
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Mobile app (new terminal)
cd apps/mobile
npm install
npx expo start
```

## Documentation

| Doc | What it covers |
|---|---|
| [docs/product.md](docs/product.md) | Problem, target users, features, user flows, requirements |
| [docs/architecture.md](docs/architecture.md) | System diagram, components, data flow, core entities |
| [docs/design.md](docs/design.md) | Design system, colors, typography, spacing, responsive rules |
| [docs/development.md](docs/development.md) | Local setup, commands, env vars, database, common workflows |
| [docs/services.md](docs/services.md) | The local services the app depends on and their config |
| [docs/decisions/](docs/decisions/) | Architecture decision records |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Branches, commits, PRs, reviews, merge rules |
| [.env.example](.env.example) | Every environment variable the project reads |

## Project layout

The code directories below are the planned layout; they will be filled in as the build starts.

```
project-root/
├── apps/
│   └── mobile/                 # Expo app (screens, components, API client)
├── server/
│   ├── app/                    # FastAPI app: routes, pipeline, models
│   ├── tests/
│   └── requirements.txt
├── assets/
│   ├── backgrounds/            # Gameplay clips (not committed, see development.md)
│   └── characters/             # Character images and voice presets
├── docs/
│   ├── product.md
│   ├── architecture.md
│   ├── design.md
│   ├── development.md
│   ├── services.md
│   └── decisions/
│       └── 001-initial-architecture.md
├── .env.example
├── CONTRIBUTING.md
└── README.md
```

## License

Open source. License to be chosen before the first public release (MIT is the current default).

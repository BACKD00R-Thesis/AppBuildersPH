# Architecture

How the system is built: its parts, how data moves through them, and the core entities. Product scope lives in [product.md](product.md); the reasoning behind these choices is in [decisions/](decisions/).

## Overview

Two processes on the user's local network:

- **Mobile app** (React Native / Expo). UI only: upload, script editing, previews, playback, and the video library.
- **Local API** (FastAPI on a laptop or desktop). Runs the AI pipeline: PDF extraction, LLM, TTS, alignment, and FFmpeg rendering.

The phone talks to the API over HTTP on the LAN. No component calls the internet at runtime.

## System diagram

```mermaid
flowchart LR
  subgraph Phone["Phone: Expo app"]
    UI[Screens & components]
    Client[API client]
    Lib[(Local video library)]
  end

  subgraph Host["Laptop: local API"]
    API[FastAPI routes]
    Jobs[Job runner]
    PDF[PDF extractor<br/>PyMuPDF]
    DB[(SQLite)]
    Files[(Data dir:<br/>PDFs, audio, renders)]
  end

  subgraph Engines["Local engines"]
    Ollama[Ollama<br/>llama3.2:3b / qwen2.5:3b]
    TTS[Kokoro-TTS / Piper]
    Whisper[faster-whisper]
    FFmpeg[FFmpeg CLI]
  end

  UI --> Client -->|HTTP over LAN| API
  API --> DB
  API --> Jobs
  Jobs --> PDF
  Jobs --> Ollama
  Jobs --> TTS
  Jobs --> Whisper
  Jobs --> FFmpeg
  Jobs --> Files
  API -->|MP4 download| Client --> Lib
```

## Components

### Mobile app (`apps/mobile`)

| Part | Responsibility |
|---|---|
| Screens | Home/library, Upload, Script editor, Style picker, Render progress, Player |
| API client | Typed wrapper over the REST API; reads the base URL from `EXPO_PUBLIC_API_URL` |
| Server connection | First-run screen to enter or scan the laptop's address; health check |
| Local library | Downloaded MP4s and their metadata stored on the device |
| Styling | NativeWind (Tailwind classes), tokens from [design.md](design.md) |

### Local API (`server/app`)

| Module | Responsibility |
|---|---|
| `routes/` | REST endpoints (see below) |
| `pipeline/extract.py` | PDF to clean text with PyMuPDF; page selection; chunking for long documents |
| `pipeline/script.py` | Prompting Ollama for a JSON dialogue; validating and repairing the output |
| `pipeline/tts.py` | Engine adapter for Kokoro or Piper; one WAV per line |
| `pipeline/align.py` | faster-whisper word timestamps for each line's audio |
| `pipeline/captions.py` | Builds an ASS subtitle file with word-by-word highlight |
| `pipeline/render.py` | FFmpeg command builder: background loop, character overlays, audio, captions |
| `jobs.py` | In-process background job queue with progress and cancellation |
| `db.py`, `models.py` | SQLite via SQLModel |

### API surface (initial)

| Method & path | Purpose |
|---|---|
| `GET /health` | Liveness, plus which engines are reachable |
| `POST /projects` | Upload a PDF; creates a project and extracts text |
| `GET /projects/{id}` | Project with its current script |
| `POST /projects/{id}/script` | Generate (or regenerate) the dialogue |
| `PUT /projects/{id}/script` | Save the user's edited lines |
| `POST /lines/{id}/preview` | Synthesize one line; returns an audio URL |
| `POST /projects/{id}/renders` | Start a render with style options |
| `GET /renders/{id}` | Status and progress (polled by the app) |
| `DELETE /renders/{id}` | Cancel a running render |
| `GET /renders/{id}/video` | Download the MP4 |
| `GET /assets/backgrounds`, `GET /assets/characters` | Available clips and personas |

Long-running work (script generation, render) returns a job ID immediately; the app polls for progress. WebSockets can replace polling later if needed.

## Data flow: PDF to video

```mermaid
sequenceDiagram
  participant App as Expo app
  participant API as FastAPI
  participant LLM as Ollama
  participant TTS as Kokoro/Piper
  participant W as faster-whisper
  participant F as FFmpeg

  App->>API: POST /projects (PDF)
  API->>API: Extract & clean text
  App->>API: POST /projects/{id}/script
  API->>LLM: Prompt with concepts + persona rules
  LLM-->>API: JSON lines [{speaker, text}]
  API-->>App: Script
  App->>API: PUT script (user edits)
  App->>API: POST /lines/{id}/preview
  API->>TTS: Synthesize one line
  API-->>App: Audio clip
  App->>API: POST /projects/{id}/renders
  loop each line
    API->>TTS: Synthesize WAV
    API->>W: Word timestamps
  end
  API->>API: Concatenate audio, build ASS captions
  API->>F: Composite background + characters + audio + captions
  F-->>API: 1080x1920 MP4
  App->>API: GET /renders/{id}/video
```

### Render composition

- **Canvas:** 1080x1920, 30 fps.
- **Background:** gameplay clip, scaled and cropped to fill, looped to the audio length, random start offset.
- **Characters:** the speaking character's image is shown (or emphasized) while their line plays, using per-line time ranges from the audio timeline.
- **Captions:** ASS subtitles burned in, one to three words per event, active word highlighted. Styles come from [design.md](design.md).
- **Audio:** per-line WAVs concatenated with a short gap, loudness-normalized.

## Core entities

```mermaid
erDiagram
  PROJECT ||--|| DOCUMENT : has
  PROJECT ||--o{ LINE : contains
  PROJECT ||--o{ RENDER : produces
  CHARACTER ||--o{ LINE : speaks
  BACKGROUND ||--o{ RENDER : used_in

  PROJECT {
    uuid id
    string title
    string status
    datetime created_at
  }
  DOCUMENT {
    uuid id
    string file_path
    int page_count
    text extracted_text
  }
  LINE {
    uuid id
    int position
    uuid character_id
    text text
    string audio_path
    json word_timestamps
  }
  CHARACTER {
    string id
    string name
    text persona_prompt
    string tts_engine
    string voice_id
    string image_path
  }
  BACKGROUND {
    string id
    string name
    string file_path
    float duration_s
  }
  RENDER {
    uuid id
    string status
    float progress
    json style_options
    string output_path
    text error
  }
```

`CHARACTER` and `BACKGROUND` are loaded from files in `assets/` at startup; the rest are SQLite tables.

## Integrations

All integrations are local processes or libraries. Details and configuration are in [services.md](services.md).

| Integration | How we call it |
|---|---|
| Ollama | HTTP API at `OLLAMA_HOST`, `format: json` for structured output |
| Kokoro-TTS / Piper | Python library (Kokoro) or CLI/library (Piper), selected by `TTS_ENGINE` |
| faster-whisper | Python library, model chosen by `WHISPER_MODEL` |
| FFmpeg | Subprocess, binary at `FFMPEG_PATH` |
| PyMuPDF | Python library for PDF text extraction |

## Cross-cutting concerns

- **Privacy:** the API binds to the LAN only. No outbound calls; CI should fail if a dependency adds telemetry we can't turn off.
- **Security:** the API has no user accounts. A shared pairing token (`API_PAIRING_TOKEN`) keeps other devices on the same network from using it.
- **Errors:** each pipeline step writes its error to the job record; the app shows it and offers a retry from the failed step.
- **Storage:** everything lives under `DATA_DIR`; deleting a project deletes its folder.

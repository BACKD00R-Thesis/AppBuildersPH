# 001: Initial architecture

- **Status:** Accepted
- **Date:** 2026-10-10

## Context

Brainrot Study turns study PDFs into short dialogue videos. The product's core promises are that it is free to use, private, and works without internet. That rules out hosted AI APIs (OpenAI, ElevenLabs) and hosted backends (Vercel, Supabase).

The pipeline needs four heavy pieces: an LLM to write the dialogue, TTS to voice it, word-level alignment for captions, and a video encoder. We have a hackathon timeline, a team comfortable with JavaScript and Python, and the demo has to run on a phone.

## Decision

1. **Split into a mobile client and a local backend.** A React Native (Expo) app handles the UI. A FastAPI server on a laptop on the same network runs the AI pipeline. They talk over HTTP on the LAN.
2. **Use Ollama for the LLM** with small 3B models (`llama3.2:3b`, `qwen2.5:3b`), requesting JSON output for the script.
3. **Use Kokoro-TTS as the primary TTS and Piper as a fallback,** behind one adapter so either can be swapped by config.
4. **Use faster-whisper for word timestamps** by transcribing each generated line, rather than relying on TTS-specific timing output.
5. **Use the FFmpeg CLI for composition,** with captions as burned-in ASS subtitles.
6. **Use SQLite for storage** and plain files under a data directory for PDFs, audio, and renders.
7. **Ship original characters and self-recorded or licensed background footage** in the repo; famous characters and copyrighted gameplay stay out.

## Alternatives considered

| Option | Why not (for now) |
|---|---|
| Cloud LLM and TTS APIs | Cost per use, needs internet, sends private notes to third parties. Breaks the core promise. |
| Fully on-device inference on the phone | 3B LLMs and FFmpeg rendering are slow or impractical on most phones, and the tooling is immature in Expo. Revisit post-MVP. |
| Desktop-only app (Electron/Tauri) | Students consume short videos on phones; the mobile app is the point of the demo. |
| Node.js backend | The best local TTS and Whisper libraries are Python-first. |
| Remotion or a JS renderer instead of FFmpeg | Heavier setup and needs a browser runtime; FFmpeg is one binary and handles everything we need. |
| Postgres / Supabase | No multi-user or sync needs; SQLite is zero-setup and file-based. |
| TTS-provided timestamps instead of Whisper | Not consistent across Kokoro and Piper; Whisper gives one alignment path for any engine. |

## Consequences

**Positive**

- Zero runtime cost and no data leaves the local network.
- Each engine sits behind a small adapter, so models can be swapped through env vars.
- Works offline once models are downloaded.

**Negative**

- Users need a laptop running the backend; the phone alone is not enough in the MVP.
- First-time setup (Ollama, FFmpeg, model downloads) is heavier than signing up for a web app.
- 3B models are less accurate than large hosted models; the script editor is the mitigation.
- Rendering speed depends on the user's hardware.

## Follow-ups

- Evaluate on-device LLM and TTS options for a phone-only mode.
- Package the backend as a one-click installer (or a Docker image) to reduce setup friction.
- Write a decision record if we ever add an optional cloud mode.

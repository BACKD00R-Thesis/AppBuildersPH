# Product

The single source of truth for what we are building and why. If a feature isn't described here, it isn't in scope.

## Elevator pitch

An open-source, 100% local AI mobile app that turns boring study PDFs into short, ultra-digestible "brainrot" educational videos: a comedic dialogue between two characters, with word-by-word captions, over gameplay footage.

## Problem

1. **Study fatigue and low retention.** Dense textbooks, lecture slides, and long PDFs are hard to digest and boring to read.
2. **Short-form attention spans.** Students already spend hours on vertical video (TikTok, Reels, Shorts) built for instant engagement. Study material doesn't come in that format.
3. **Cloud cost and privacy.** Current AI study tools depend on paid, internet-connected APIs. They are slow on bad connections, cost money per use, and send private notes and course material to third parties.

## Target users

| User | Context | What they need |
|---|---|---|
| **Primary: university and senior high school students** | Cramming before exams, often on a phone, sometimes with poor connectivity | A fast way to get the gist of a chapter in a format they will actually watch |
| **Secondary: teachers and student org tutors** | Making review material for a class | Quick, shareable explainer clips from their own slides |
| **Secondary: privacy-conscious learners** | Working with unpublished research or confidential notes | AI help that never uploads their documents |

## Solution

An offline-first React Native app paired with a local AI backend. It ingests a PDF, converts the key concepts into an ELI5 dialogue between two personas, and renders a fully composited 9:16 video with animated captions. Every model runs on the user's own machine or local network.

## Core user flow

```
[ Upload PDF / notes ] ──> [ Edit AI script ] ──> [ Customize style ] ──> [ Export & watch ]
```

1. **Upload.** The user taps to import a lecture deck, paper, or textbook chapter (PDF). They can optionally pick the pages or section to cover.
2. **Script generation.** The local LLM extracts the core concepts and writes a dialogue. One character asks simple, slightly clueless questions; the other gives concise ELI5 answers with everyday analogies.
3. **Customize and preview.** The user reviews each line, edits text, reorders or deletes lines, taps a line to hear a voice preview, and picks a background clip.
4. **Render and export.** The backend synthesizes the audio, aligns word-level timestamps, burns in captions, and renders a 9:16 MP4. The user watches it in-app and can save or share it.

## Features

### MVP (hackathon demo)

| Feature | Description |
|---|---|
| PDF import | Pick a PDF from the device; extract its text. |
| ELI5 dialogue engine | Generate a two-character script (target 45 to 90 seconds of speech) from the extracted text. |
| Script editor | Edit, delete, and reorder lines; regenerate the whole script. |
| Voice preview | Synthesize and play a single line on demand. |
| Background picker | Choose from a few bundled gameplay clips. |
| Brainrot captions | Word-by-word highlighted captions, timed to the audio. |
| Render and export | Produce a 1080x1920 MP4 and show render progress. |
| Video library | List past renders on the device and replay them. |

### Post-MVP

- Regenerate a single line instead of the whole script.
- Custom personas: name, personality prompt, voice, and image.
- Import from images (OCR) and plain text, not only PDF.
- Split long documents into a series of short episodes.
- Quiz cards generated from the same script.
- Fully on-device mode for high-end phones (no laptop needed).

## Requirements

### Functional

- **FR-1** The app accepts PDFs up to 50 pages / 20 MB.
- **FR-2** Script generation returns a structured list of lines, each with a speaker and text.
- **FR-3** Every line in the script can be edited before rendering; edits are saved.
- **FR-4** A voice preview for a single line plays within 3 seconds on reference hardware.
- **FR-5** Rendered videos are 1080x1920, H.264 + AAC, MP4.
- **FR-6** Captions show one to three words at a time with the active word highlighted.
- **FR-7** The user can see render progress and cancel a render.

### Non-functional

- **Privacy:** no network calls leave the local network. No telemetry, no cloud APIs.
- **Cost:** zero per-use cost. All models are free and open-weight.
- **Performance:** a 60-second video renders in under 3 minutes on reference hardware (a laptop with 16 GB RAM; GPU optional).
- **Reliability:** a failed step (LLM, TTS, render) reports a clear error and can be retried without losing the script.
- **Offline:** after first-time model downloads, every feature works with Wi-Fi off (phone and laptop on the same hotspot or LAN).

## Success metrics

- Time from upload to finished video under 5 minutes for a 10-page PDF.
- Test users can correctly answer at least 3 of 5 questions about the source material after watching.
- In the demo, judges understand what the app does within the first 10 seconds of a sample video.

## Risks and open questions

- **Character IP.** The pitch references Peter and Stewie Griffin. Those characters, and voice clones of their actors, are copyrighted. For the public repo and any release, we ship original personas with stock TTS voices; recognizable characters stay out of the codebase.
- **Gameplay footage licensing.** Minecraft parkour and Subway Surfers clips belong to their publishers. We bundle only footage we recorded ourselves or that is licensed for reuse, and let users add their own clips locally.
- **Accuracy.** Small 3B models can oversimplify or get facts wrong. The script editor exists so the user can fix this; we should also show a short disclaimer on generated scripts.
- **Phone vs. laptop.** The MVP runs the AI backend on a laptop on the same network. Fully on-device inference is a post-MVP goal. See [decisions/001-initial-architecture.md](decisions/001-initial-architecture.md).

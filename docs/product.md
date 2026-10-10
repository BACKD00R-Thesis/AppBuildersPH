# Product

The single source of truth for what we are building and why. If a feature isn't described here, it isn't in scope.

## Elevator pitch

An open-source, 100% local AI app, for laptop and phone, that turns boring study PDFs into short, ultra-digestible "brainrot" educational videos: Bunso asks and Tito explains the material in a short, funny dialogue, with word-by-word captions, over gameplay footage.

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

A web app served by a local AI engine on the student's laptop, usable from the laptop or from a phone on the same Wi-Fi. It ingests a PDF or pasted notes, picks out the key ideas, turns them into an ELI5 dialogue between Bunso (asks) and Tito (explains), and renders a fully composited 9:16 video with animated captions. Every model runs on the user's own machine. The screens follow the Figma file linked in [design.md](design.md).

## Core user flow

```
[ Upload PDF / notes ] ──> [ Edit AI script ] ──> [ Customize style ] ──> [ Export & watch ]
```

1. **Upload.** The user picks a lecture deck, paper, or textbook chapter (PDF, .txt or .md) or pastes notes, chooses a length (30, 60 or 90 seconds) and whether to use Taglish. On a laptop, dropping a file on "Make a video" starts right away.
2. **Script generation.** The local LLM finds the key ideas (3, 5 or 8 by length), then writes a dialogue: Bunso, a curious 10-year-old, opens with the dumb-but-real question; Tito, a patient tito, answers each idea with one everyday analogy; Bunso closes by saying it back in her own words. The app shows each step while it works.
3. **Customize and preview.** The user taps a line to edit it, adds lines, plays any line in its voice, hears a sample of each voice, and picks a background and caption style (Bold pop, Clean, Outline) with a live preview.
4. **Render and export.** The engine voices the lines, aligns word-level timestamps, burns in captions, and renders a 9:16 MP4 while the app shows progress. The user watches it with the key ideas listed beside it, then downloads or shares it.

## Features

### MVP (hackathon demo)

| Feature | Description |
|---|---|
| Sources | PDF, .txt or .md file, or pasted notes. |
| Length and language | 30, 60 or 90 seconds; English or Taglish (English explanations, Filipino reactions). |
| ELI5 dialogue engine | Key ideas first, then a Bunso and Tito script that covers them in order. |
| Script editor | Edit lines inline (saved automatically), add lines, regenerate the whole script. Clearing a line's text removes it. |
| Voice preview | Play any line, or a sample of each voice. |
| Style | Four backgrounds (clip or matching gradient), three caption styles, live 9:16 preview. |
| Brainrot captions | Two-line captions with the spoken word in mustard, at a readable 2.5 to 3 words per second. |
| Render and export | 1080x1920 MP4 with step-by-step progress; download, share (phones), or open the folder (laptop). |
| Library | Every video with its status; the newest finished one featured on the phone's Home. |
| Key ideas | "What this video covers" next to the player. |

### Post-MVP

- Regenerate a single line instead of the whole script; reorder and switch speakers in the editor.
- Custom personas: name, personality prompt, voice, and image.
- Import from images (OCR) and slides (.pptx).
- Split long documents into a series of short episodes.
- Quiz cards generated from the key ideas.
- Installable PWA, and the Engine and Library-tab screens once they're designed.
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

- **Character IP.** The pitch references Peter and Stewie Griffin. Those characters, and voice clones of their actors, are copyrighted. We ship original personas, Tito and Bunso, with stock TTS voices; recognizable characters stay out of the codebase.
- **Gameplay footage licensing.** Minecraft parkour and Subway Surfers clips belong to their publishers. We bundle only footage we recorded ourselves or that is licensed for reuse, and let users add their own clips locally.
- **Accuracy.** Small 3B models can oversimplify or get facts wrong. The script editor exists so the user can fix this; we should also show a short disclaimer on generated scripts.
- **Phone vs. laptop.** The MVP runs the AI backend on a laptop on the same network. Fully on-device inference is a post-MVP goal. See [decisions/001-initial-architecture.md](decisions/001-initial-architecture.md).

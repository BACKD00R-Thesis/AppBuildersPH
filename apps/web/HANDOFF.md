# Brainrot Study UI: handoff

Frontend for the Figma file "Brainrot Study - Mockups", pages **Laptop v2** and **Mobile v2**.
All 11 screens are built and wired to the local engine (`server/`): real videos, scripts, voices, renders.

Figma: https://www.figma.com/design/XZ1j6rFGLywINmdEWMBaAF/Brainrot-Study---Mockups

## Run

The engine must be running (see [docs/development.md](../../docs/development.md)).

```bash
npm install
npm run dev      # http://localhost:5173 (also on your Wi-Fi address); /api is proxied to the engine
npm run build    # type-check + production build into dist/, which the engine serves at http://<laptop>:8000
```

Needs Node 20.19+ or 22.12+ (Vite 8). `ENGINE_URL` changes where `npm run dev` proxies (default `http://localhost:8000`).
Open `/_screens` for a list of every screen for the newest video.

## Stack

React 19, TypeScript, Vite 8, Tailwind CSS 4 (tokens in `src/index.css`, no `tailwind.config`), React Router 7.
Fonts are bundled through `@fontsource/*`, so the app works offline.

## Routes

One URL per step. The window width picks the design: laptop at 1180px and wider, mobile below.
A video's `:id` is the engine's project id.

| URL | Laptop (Figma node) | Mobile (Figma node) |
|---|---|---|
| `/` | Library (9:12) | Home (14:12) |
| `/new` | no design, redirects to `/` | Upload (14:99) |
| `/videos/:id/writing` | no design, redirects to script | Writing script (14:146) |
| `/videos/:id/script` | Workspace (9:116) | Script editor (14:200) |
| `/videos/:id/style` | part of Workspace, redirects | Style (14:270) |
| `/videos/:id/rendering` | Rendering (9:290) | Rendering (14:347) |
| `/videos/:id` | Player (9:360) | Player (14:387) |

Lists link each video to the step it's at (`videoHref` in `lib/videos.ts`): writing, script, rendering or player.
Writing script moves on to the script when the engine finishes; Rendering moves on to the player.

## Where things are

```
src/
  index.css            design tokens (colors, fonts, shadows, radii)
  App.tsx              route table
  lib/
    api.ts             typed client for the engine's /api (and the pairing token)
    store.tsx          app-wide: library, engine health, backgrounds, new-video draft, startNewVideo
    useProject.ts      one video: load, poll while busy, style/regenerate/render actions
    videos.ts          engine project -> video card; step routing; step lists for the progress screens
    audio.ts           one shared player for line previews and voice samples
    options.ts         caption styles, lengths, key-idea counts per length
    speakers.ts        Tito Boy and Bunso display names, initials and vibes
    types.ts, format.ts, cn.ts, useIsDesktop.ts
  components/          Button, Avatar, VideoFrame, VideoPlayer, ScriptLineCard, ScriptList (+ editing hook),
                       ScriptProgress, Segmented, Toggle, Steps, ProgressBar, KeyIdeas, Notice, Icon
  layouts/             DesktopShell (sidebar, file picker, engine card), MobileShell, TabBar
  screens/desktop/     Library, Workspace, Rendering, Player
  screens/mobile/      Home, Upload, WritingScript, ScriptEditor, Style, Rendering, Player
  assets/icons/        SVGs exported from Figma, unmodified
design-reference/mobile/   Figma renders of the 7 mobile screens
```

## How it talks to the engine

| UI action | Engine call |
|---|---|
| Upload "Write the script", laptop "New video" / drop | `POST /api/projects` (file or notes, length, Taglish), then `POST /api/projects/:id/script` |
| Writing script progress | polls `GET /api/projects/:id` (`script_step`: ideas, jokes, check) |
| Edit a line, "Done" / Enter | `PUT /api/projects/:id/script` (lines left empty are dropped) |
| Play a line | saves if needed, `POST /api/lines/:id/preview`, plays the returned WAV |
| Hear sample | `GET /api/assets/characters/:id/sample` |
| Background, captions, Taglish | `PATCH /api/projects/:id` (saved per video) |
| Regenerate | `POST /api/projects/:id/script` (asks first on laptop, since it replaces edits) |
| Render video | `POST /api/projects/:id/renders`, then polls for `step` and `progress` |
| Player | `<video>` of `/api/renders/:id/video`; Download adds `?download=1`; Share uses the Web Share API; Open folder is `POST /api/renders/:id/reveal` |

## Design rules (from the Figma style sheet)

- Serif (Playfair Display) only for headings and big numbers. Sans (Plus Jakarta Sans) for everything you read or click.
- Mustard is the single highlight: one badge or one caption word at a time.
- Arches appear in headers and empty states only, never behind text.
- Buttons are pills. Cards 20px radius. Inputs 14px. Text never below 13px (12px is used for small labels in the mockups).
- Archivo Black, outlines and mustard captions live inside `VideoFrame` only. "Brainrot stays in here."
- Use the token classes (`bg-green`, `text-muted`, `bg-mint`, `shadow-card`, `rounded-card`, `font-serif`, ...).
  The default Tailwind palette is disabled on purpose.

## What differs from Figma, and why

- **Device chrome is not rendered.** The phone bezel, the "9:41 / 5G 83%" status bar and the 2px laptop window
  border are mockup framing. Mobile headers start at the safe-area inset instead, so they sit 26px higher than in the frames.
- **Content is real.** Greeting name comes from the engine's `USER_NAME` ("Kumusta!" without one); subjects, titles,
  line counts, durations and key ideas come from the script; "N videos this week" counts renders from the last 7 days.
- **Thumbnails and previews** use the design's `VideoFrame` with a caption made from the title (lists) or the first
  script line (previews, so "Updates as you edit" is literal). The players show the real MP4 instead.
- **Script lines start idle.** The "playing" and "editing" cards in the frames are states; click play or the text to see them.
- **The laptop player video shrinks on short screens** (below 784px tall) instead of scrolling. It is 405x720 at 900px tall, as designed.
- **Laptop Workspace needs about 850px of height**; shorter windows scroll.
- **Writing script: "Back to home" instead of "Cancel".** The engine can't stop a script mid-way, so the button only leaves.
  When writing fails, it becomes "Try again".
- **Rendering: "Try again"** appears next to "Back to script" when a render fails or is canceled.
- **Mobile Player has an "Edit script" link** under the buttons, like the laptop player; otherwise there was no way back to the script.
- **Upload accepts PDF, .txt and .md** (the mockup listed slides too; the engine can't read .ppt/.pptx yet), shows the
  file size instead of a page count (pages are only known after upload), and has "Remove file" so notes can be used instead.

## Not designed yet (built minimally from existing tokens, not invented)

- Errors and empty states: `Notice` (mint card, clay text, one text action).
- Laptop sidebar engine card: "Checking the engine…", "Engine running", "Engine needs setup" (lists what's missing), "Engine offline".
- Voice loading: the play button pulses and the line reads "Getting the voice…".
- Engine screen, and the mobile Library tab: nav items are shown but are not links.
- Laptop upload and "writing script" screens: on laptop, "New video" and the "Make a video" pill open the file
  picker, start the script with 60s and Taglish on, and show progress inside the Workspace's script column.
- Toggle off state: `toggle-off.svg` is the only icon not exported from Figma.
- "Clean" and "Outline" caption styles: selectable and rendered by the engine, but the in-app preview only draws "Bold pop".
- Key-idea counts for 30s and 90s (3 and 8): only 60s (5) is in the design; the engine uses the same numbers.
- Deleting, reordering or re-assigning lines: not in the design. Clearing a line's text and pressing Done removes it.
- Hover and focus states: primary buttons hover to `green-2` per the style sheet; the rest are minimal.

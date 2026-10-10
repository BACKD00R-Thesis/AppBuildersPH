# Design

The visual source of truth for the app and the rendered videos. When this doc, the Figma file and a screen disagree, fix one of them.

## Figma

- **File:** [Brainrot Study - Mockups](https://www.figma.com/design/XZ1j6rFGLywINmdEWMBaAF/Brainrot-Study---Mockups), pages **Laptop v2** and **Mobile v2**, plus the style sheet.
- **Built in:** `apps/web`. [apps/web/HANDOFF.md](../apps/web/HANDOFF.md) maps every route to its Figma frame and lists what differs from the file and why. Renders of the mobile frames are in `apps/web/design-reference/mobile/`.

## Design principles

1. **Brainrot stays in the video.** The app is calm (serif headings, soft greens, arches); the loud look (Archivo Black, outlines, mustard captions) appears only inside video frames.
2. **Mustard is the single highlight:** one badge or one caption word at a time.
3. **Always show progress.** Script writing and rendering take time; show steps, a percentage, and what happens next.

## Color tokens

Defined in `apps/web/src/index.css` (Tailwind 4 `@theme`). The default Tailwind palette is disabled on purpose: use these names.

| Token | Value | Use |
|---|---|---|
| `green` | `#1E4A35` | Headers, primary buttons |
| `green-2` | `#2F6B4F` | Hover, chips, eyebrow text |
| `green-3` | `#8FB59E` | Progress track |
| `page` | `#F4F7F3` | Background |
| `mint` | `#E8EFE8` | Rows, Tito's lines |
| `mint-line` | `#D5E3D7` | Borders |
| `card` | `#FCFDFB` | Cards, Bunso's lines |
| `ink` | `#17221C` | Text |
| `muted` | `#5E6B63` | Secondary text |
| `mustard` | `#E8B23A` | The one highlight |
| `clay`, `clay-2` | `#C97A4A`, `#E0A06E` | Arches only (and error text, `clay-deep`) |
| `on-green` | `#B9D2C2` | Secondary text on green |
| `video` | `#151A14` | Video base, caption outline |

## Typography

| Font | Use |
|---|---|
| Playfair Display (600, 700) | Headings and big numbers only |
| Plus Jakarta Sans (500, 600, 700) | Everything you read or click |
| Archivo Black | Video captions only |

Fonts are bundled through `@fontsource/*` so the app works offline. Text never goes below 12 px.

## Shape

- Buttons are pills. Cards have a 20 px radius, inputs 14 px.
- Arches appear in headers and empty states only, never behind text.
- Shadows: `shadow-card` (laptop), `shadow-card-sm` (phone).

## Layouts

- **Laptop** (1180 px and wider): sidebar (Library, New video, Engine status) and main area. The Workspace puts script, live 9:16 preview and style side by side.
- **Phone** (below 1180 px, max 480 px wide): green header, page-colored sheet with 28 px top corners, pinned bottom bar. Respects safe-area insets.

## States not in Figma

Kept deliberately quiet and built from existing tokens:

| State | Treatment |
|---|---|
| Errors (engine offline, script failed, render failed) | Mint card with `clay-deep` text and a text action ("Retry", "Try again") |
| Empty library | Mint card with muted text pointing to "Make a video" |
| Engine card (laptop sidebar) | "Engine running" with the green dot; otherwise a clay dot and what's missing |
| Line voice loading | Play button pulses; meta text reads "Getting the voice…" |

## Video style (rendered output)

- **Frame:** 1080x1920, 9:16, 30 fps.
- **Background:** the chosen gameplay clip, or its gradient (same colors as the app's previews) with a 5% white floor band from 64% down, matching `VideoFrame`.
- **Layout:** from the mascot sheet ("Tito and Bunso Mascots" in Claude Design). Both characters stand along the bottom edge, Tito (explainer) on the left and Bunso (asker) on the right; the speaker is full color, the listener is dimmed to 55%, 94% size and sits lower. Each line sets both expressions: Bunso is bored on the hook, curious while asking or listening, "gets it" on the recall and hyped at Tito's dad joke; Tito explains (every third line he thinks), laughs on his last line and is chill while listening. Captions are centered at y=1000 with the speaker's name just above (y=830). The characters reach into the bottom 320 px platform-UI zone, as in the sheet.
- **Captions:** uppercase, up to two lines of up to three words (16 characters) each; extra words go on the second line. A line ends after a comma, a block at the end of a sentence. The spoken word is mustard; no size change, so text never shifts. One block on screen at a time.
  - **Bold pop** (default): Archivo Black 84 px, white, 7 px `video` outline, soft shadow.
  - **Clean:** Plus Jakarta Sans 70 px, white on a translucent `video` box.
  - **Outline:** Archivo Black 84 px, hollow white letters; the spoken word fills in mustard.
- **Speakers:** Tito's name in his orange (`#F08A3C`), Bunso's in her pink (`#F27BA5`), the `color` in the character manifest.
- **Pace:** speech, and therefore the captions, runs at 2.5 to 3 words per second. Lines read faster or slower are time-stretched (pitch preserved) to 2.75; lines under four words are left as they are.
- **Safe zones:** captions stay out of the bottom 320 px and the right 140 px, where TikTok/Reels/Shorts overlay their buttons. The characters deliberately reach into that zone (see Layout).

## Accessibility

- Icon-only buttons have labels; toggles and segmented controls use switch/radio roles.
- Voice previews show a playing state, not only sound.
- Focus rings use `green-2`.
- Rendered captions are part of the video, so it's understandable without audio.

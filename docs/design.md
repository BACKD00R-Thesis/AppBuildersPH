# Design

The visual source of truth for the app UI and the rendered videos. When this doc and a screen disagree, fix one of them.

## Figma

- **Figma file:** _TBD, add the link here once the file is created._
- Components in Figma use the same token names as this doc and `tailwind.config.js`.

## Design principles

1. **Loud on the video, calm in the app.** The rendered video is high-energy; the editor around it is clean so students can focus on the script.
2. **Thumb-first.** Every primary action is reachable with one thumb at the bottom of the screen.
3. **Always show progress.** Generation and rendering take time; never leave the user looking at a frozen screen.

## Color tokens

Defined as NativeWind theme extensions. Dark mode is the default.

| Token | Dark | Light | Use |
|---|---|---|---|
| `bg` | `#0E0E12` | `#FAFAFC` | App background |
| `surface` | `#1A1A22` | `#FFFFFF` | Cards, sheets, inputs |
| `surface-2` | `#24242E` | `#F0F0F5` | Pressed states, nested surfaces |
| `border` | `#2E2E3A` | `#E2E2EA` | Dividers, input borders |
| `text` | `#F5F5F7` | `#111117` | Primary text |
| `text-muted` | `#A0A0AE` | `#5C5C6B` | Secondary text, hints |
| `primary` | `#B6FF3B` | `#5BA300` | Primary buttons, active states |
| `on-primary` | `#0E0E12` | `#FFFFFF` | Text on primary |
| `accent` | `#FF3BD4` | `#C4009E` | Highlights, badges |
| `speaker-a` | `#3BC8FF` | `#0077A8` | Character A's lines in the editor |
| `speaker-b` | `#FFB23B` | `#B36B00` | Character B's lines in the editor |
| `danger` | `#FF4D4D` | `#D11A1A` | Errors, destructive actions |
| `success` | `#3BFF8A` | `#0A8A3F` | Completed renders |

Every text/background pair must meet WCAG AA contrast (4.5:1 for body text, 3:1 for large text).

## Typography

| Token | Font | Size / line height | Weight | Use |
|---|---|---|---|---|
| `display` | Inter | 32 / 38 | 800 | Screen titles |
| `title` | Inter | 22 / 28 | 700 | Section headers |
| `body` | Inter | 16 / 24 | 400 | Script lines, body text |
| `label` | Inter | 14 / 20 | 600 | Buttons, chips |
| `caption` | Inter | 12 / 16 | 500 | Meta info, timestamps |

Fonts are bundled with the app (no runtime downloads) via `expo-font`.

## Spacing, radius, and elevation

- **Spacing scale:** 4-point grid: 4, 8, 12, 16, 24, 32, 48. Screen side padding is 16.
- **Radius:** `sm` 8 (chips, inputs), `md` 12 (cards), `lg` 20 (bottom sheets), `full` (pill buttons, avatars).
- **Elevation:** dark mode uses surface color steps instead of shadows; light mode uses one soft shadow for sheets.
- **Touch targets:** at least 44x44.

## Key components

| Component | Notes |
|---|---|
| Primary button | Full-width pill, `primary` fill, fixed to the bottom safe area on flow screens |
| Script line card | Speaker avatar + name in the speaker color, editable text, play-preview button, drag handle |
| Background picker | Horizontal carousel of looping muted thumbnails, selected item outlined in `primary` |
| Progress panel | Step list (Extract, Script, Voices, Captions, Render) with current step and percentage |
| Empty state | Illustration, one sentence, one action |

## Video style (rendered output)

The rendered video has its own style, independent of app theme.

- **Frame:** 1080x1920, 9:16, 30 fps.
- **Layout:** background gameplay fills the frame; the speaking character (520 px tall, top at y=290) sits in the upper third with their name above; captions are centered at y=1000, just below the character, so platform UI doesn't cover them.
- **Captions:** heavy sans (Montserrat ExtraBold or similar, bundled), around 90 px, white fill, 8 px black outline, uppercase. The active word turns `primary` (`#B6FF3B`) with a slight scale-up. One to three words on screen at a time.
- **Safe zones:** keep captions and characters out of the bottom 320 px and the right 140 px, where TikTok/Reels/Shorts overlay their buttons.

## Responsive rules

- Design at 390x844 (a typical phone); test at 360x640 and 430x932.
- Tablets: center content in a max-width 600 column; the script editor can show the preview player beside the list in landscape.
- Support system font scaling up to 200%; script line cards grow vertically and never truncate the text.
- Respect safe-area insets on all edges.

## Accessibility

- Every icon-only button has an accessibility label.
- Voice previews have a visible playing state, not only sound.
- Rendered captions are part of the video, so the video is understandable without audio.

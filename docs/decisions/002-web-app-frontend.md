# 002: Web app instead of the Expo app

- **Status:** Accepted
- **Date:** 2026-10-10
- **Supersedes:** the "React Native (Expo) mobile app" part of [001](001-initial-architecture.md)

## Context

The first frontend was an Expo (React Native) app that talked to the local engine over the LAN. Since then the team designed the product in Figma ("Brainrot Study - Mockups", pages **Laptop v2** and **Mobile v2**) and built those designs as a React web app with mock data (`brainrot-study-ui`).

The designs cover both a laptop layout (sidebar, three-column workspace) and a phone layout. The engine always runs on a laptop anyway, so the laptop is a first-class place to make videos, not only the phone.

## Decision

1. **The frontend is the Figma-built web app**, in `apps/web` (React 19, Vite, Tailwind CSS 4, React Router). One URL per step; the window width picks the laptop (1180 px and up) or phone design.
2. **The engine serves it.** FastAPI keeps the REST API under `/api` and serves the built app (`apps/web/dist`) at `/`, with index.html for client-side routes. A phone or laptop on the same Wi-Fi opens `http://<laptop-ip>:8000`; there is no app to install and no server address to type in.
3. **The Expo app is removed** (`apps/mobile`). It stays in git history.
4. **The engine grew to match the design:** Tito Boy and Bunso as the cast, pasted notes and .txt/.md as sources, video length (30/60/90 s), Taglish mode, key ideas ("What this video covers"), a subject label, three caption styles, gradient backgrounds that match the in-app previews, and voice samples.

## Alternatives considered

| Option | Why not |
|---|---|
| Port the Figma designs to the Expo app | Two layouts' worth of pixel work in React Native, and the laptop layout fits a browser far better. The web build already matched the Figma. |
| Keep both frontends | Two codebases to keep in sync with one API for a hackathon team. |
| Separate web server for the frontend | Another process and port, plus CORS and a server-address setting. Same-origin serving removes all three. |

## Consequences

**Positive**

- One codebase for laptop and phone, matching the Figma.
- No install on phones; nothing to configure: the app and the engine share an origin.
- Media (audio previews, videos) plays with plain `<audio>`/`<video>` elements.

**Negative**

- No native features: videos are saved through the browser's download or share sheet instead of the photo library.
- Phones need the laptop on the same network to use the app at all (this was already true for the AI work).
- Offline phone playback of saved videos now depends on the phone's own downloads, not an in-app library.

## Follow-ups

- Installable PWA (manifest + service worker) so the app opens like a native one on phones.
- Engine and Library-tab screens once they're designed.

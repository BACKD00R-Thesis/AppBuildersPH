# Contributing

How we work together on Brainrot Study. Setup instructions are in [docs/development.md](docs/development.md).

## Ground rules

- `main` is always demo-ready. If `main` is broken, fixing it is everyone's top priority.
- Nothing calls a cloud API. If a change needs one, write a decision record first ([docs/decisions/](docs/decisions/)).
- Never commit secrets, `.env`, model weights, user PDFs, rendered videos, or copyrighted footage or characters.
- Docs are part of the change: if you change setup, env vars, the API, or the design system, update the matching doc in the same PR.

## Branches

Branch from `main`. Name branches `<type>/<short-description>`:

| Type | Use for | Example |
|---|---|---|
| `feat/` | New features | `feat/voice-preview` |
| `fix/` | Bug fixes | `fix/caption-timing-drift` |
| `docs/` | Documentation only | `docs/setup-windows` |
| `refactor/` | Code changes with no behavior change | `refactor/tts-adapter` |
| `chore/` | Tooling, dependencies, CI | `chore/bump-expo` |

Keep branches short-lived (ideally under two days during the hackathon). Rebase on `main` before opening a PR if you've fallen behind.

## Commits

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <summary in the imperative, under 72 chars>

<optional body: what and why, not how>
```

- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`.
- Scopes: `mobile`, `server`, `pipeline`, `docs`, `ci`.
- Examples: `feat(pipeline): add word-level ASS captions`, `fix(mobile): keep script edits after app reload`.

One logical change per commit. Don't mix formatting changes with behavior changes.

## Pull requests

1. Open a PR against `main`. Use a draft PR if you want early feedback.
2. Title follows the commit format (`feat(mobile): ...`).
3. Description includes:
   - **What** changed and **why** (link the issue: `Closes #12`).
   - **How to test** it, step by step.
   - **Screenshots or a short clip** for any UI or video-output change.
4. Keep PRs small, around 400 changed lines or fewer. Split bigger work.
5. Checks must pass: lint, type check, and tests for the parts you touched.

### Checklist

- [ ] Runs locally (backend and app)
- [ ] Tests added or updated
- [ ] Docs and `.env.example` updated if needed
- [ ] No secrets, large binaries, or copyrighted assets added

## Reviews

- Every PR needs **one approving review** from someone other than the author.
- Reviewers respond within a few hours during the hackathon, and within one working day afterwards.
- Review for correctness, clarity, and fit with the docs. Prefix optional suggestions with `nit:`.
- The author resolves conversations they've addressed; the reviewer resolves anything they raised that is still open.
- Changes to [docs/architecture.md](docs/architecture.md) or [docs/decisions/](docs/decisions/) need a review from a second team member as well.

## Merging

- **Squash and merge** so each PR is one commit on `main`, with the PR title as the commit message.
- The author merges once approved and checks are green.
- Delete the branch after merging.
- No direct pushes to `main`; enable branch protection for it.
- If a merge breaks `main`, revert first and fix in a new PR.

## Issues

- Use labels: `bug`, `feature`, `docs`, `good first issue`, plus `mobile` or `server`.
- Bugs include steps to reproduce, expected vs. actual behavior, and device/OS.
- Assign yourself before starting work so two people don't take the same task.

## Decision records

For any important technical choice (new dependency category, new service, data model change, change to the offline promise):

1. Copy the latest file in [docs/decisions/](docs/decisions/) to the next number, e.g. `002-short-title.md`.
2. Fill in Context, Decision, Alternatives considered, and Consequences.
3. Open it as its own PR, or together with the change it explains.

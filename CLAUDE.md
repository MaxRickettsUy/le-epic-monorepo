# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A genre-scoped music archive (a hardcore-punk "Metal Archives"). Two independently-run
apps in one repo, with **no root tooling** — `cd` into the one you're working on:

- `backend/` — FastAPI + SQLAlchemy + Postgres API. Owns all data; seeded from a
  MusicBrainz database dump.
- `app/` — Next.js 15 (App Router, React 19) frontend. Owns **no** data; a pure
  HTTP client of the backend.

The frontend⇄backend HTTP contract is documented in `app/docs/api-contract.md` and
is the thing to read first before changing any request/response shape.

## Commands

### Backend (`cd backend`)

```bash
docker compose up --build      # run Postgres + API; API on localhost:8000, docs at /docs
pytest                         # run tests (in-memory SQLite, no Postgres needed)
pytest tests/test_band.py      # single test file
pytest tests/test_band.py::test_name   # single test
ruff check .                   # lint
ruff check . --fix             # lint + autofix
ruff format .                  # format
```

Install dev deps with `pip install -r requirements-dev.txt`. Migrations run via
`alembic -c migrations/alembic.ini upgrade head` (the Docker `boot.sh` does this on
container start). New migration: `alembic -c migrations/alembic.ini revision --autogenerate -m "..."`.

Seeding (requires a separate MusicBrainz Postgres — see `backend/README.md`):
```bash
python -m seed.mb_dump      # upsert bands/albums/members by MBID (idempotent)
python -m seed.cover_art    # fill album.art from the Cover Art Archive
```

### Frontend (`cd app`)

```bash
npm run dev          # dev server (Turbopack) on localhost:3000
npm run build        # production build
npm run lint         # ESLint (next/core-web-vitals + prettier)
npm run typecheck    # tsc --noEmit
npm run format       # prettier --write
```

## Backend architecture

- **App factory** in `app/__init__.py`: `app = FastAPI(...)`, mounts routers under
  `/band`, `/release`, `/track`, adds CORS. Note the package and the FastAPI instance
  share the name `app` — tests access the instance via `app_pkg.app` (see
  `tests/conftest.py`), not `from app import app`.
- **Per-domain routers** in `app/{band,release,track}/routes.py`. Each uses the
  `get_db` dependency (`app/database.py`) for a per-request SQLAlchemy session.
- **Models** (`app/models.py`) use SQLAlchemy 2.0 typed `Mapped[...]` columns and a
  `TimestampMixin`. Important naming history: the `Release` model/table was renamed to
  `Album`, but **the wire/JSON shape was deliberately kept unchanged** — `Band.releases`,
  `Track.release_id`/`release` still use the old names. Don't "fix" these without
  updating the contract.
- **Schemas** (`app/schemas.py`) are Pydantic. `ORMModel` enables `from_attributes`;
  `BaseInput` sets `extra="forbid"` so write bodies reject unknown fields with a 422.
- **Settings** (`app/settings.py`) via pydantic-settings from env/`.env`. `cors_origins`
  is comma-separated (`*` allows all but disables credentials).
- **MusicBrainz** access is isolated in `app/services/musicbrainz.py` (web-API lookups)
  and `seed/` (bulk dump import). The API itself never calls MusicBrainz except the
  `/band/search*` endpoints.
- **Reviews/Users are out of MVP** and intentionally unmodeled (legacy tables dropped in
  the Phase 3 migration). `avg_review`/`review_count` are hardcoded to 0.

## Frontend architecture

- **App Router, server-first.** Pages are Server Components that fetch directly from the
  backend; there is no client-side data fetching of app data.
- **Typed data layer** in `lib/api/`: `client.ts` (`apiFetch`/`apiFetchOrNull`) is the
  single network boundary. `API_URL` is **server-only** (never `NEXT_PUBLIC_`). A 404 in
  `apiFetchOrNull` resolves to `null` so pages render `not-found.tsx`.
- **Every response is validated** against a zod schema in `lib/schemas/index.ts` at the
  client boundary; a mismatch throws `ApiParseError` → nearest `error.tsx`. These zod
  schemas mirror `backend/app/schemas.py` and are the source of truth for TS types
  (`lib/types.ts` re-exports inferred types). **When you change a backend schema, update
  the matching zod schema and `app/docs/api-contract.md`.**
- **Writes go through Server Actions** in `app/actions.ts` (which call `lib/api/*`, then
  `revalidatePath` + `redirect`). Forms use `@tanstack/react-form` (`components/forms/`).
- **UI**: shadcn/ui (Radix + CVA) in `components/ui/`, Tailwind, `next-themes` dark mode.
  Path alias `@/*` maps to the `app/` root. Remote image hosts are allowlisted in
  `next.config.mjs` (set `NEXT_PUBLIC_ART_HOST` for art CDN).

## Conventions

- Wire/DB fields are `snake_case`, in TS types too.
- Multi-phase work is tracked in `backend/plans/resurrection.md` and
  `app/plans/upgrade-plan.md` (referenced throughout code comments as "Phase N").

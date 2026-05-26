# le-epic-monorepo

A genre-scoped music archive — a hardcore-punk take on Metal Archives. Browse bands,
their discographies, releases, tracks, and members, all seeded from a
[MusicBrainz](https://musicbrainz.org/) database dump.

The repo holds two independently-run apps:

| Directory  | Stack                                          | Role                                            |
| ---------- | ---------------------------------------------- | ----------------------------------------------- |
| `backend/` | FastAPI · SQLAlchemy 2.0 · Postgres · Alembic  | Owns all data; serves the JSON API.             |
| `app/`     | Next.js 15 (App Router) · React 19 · Tailwind  | Pure HTTP client of the backend; owns no data.  |

There is no root-level tooling — each app is built, run, and tested on its own. The
frontend⇄backend HTTP contract is documented in [`app/docs/api-contract.md`](app/docs/api-contract.md).

## Quick start

### 1. Backend (API + Postgres)

```bash
cd backend
cp .env.example .env          # adjust as needed
docker compose up --build
```

The API comes up on `http://localhost:8000`, with interactive docs at `/docs`.
Migrations run automatically on container start.

### 2. Frontend

```bash
cd app
npm install
cp .env.example .env.local    # API_URL defaults to http://127.0.0.1:8000
npm run dev
```

Open `http://localhost:3000`.

## Seeding data

The catalogue is seeded from a local MusicBrainz Postgres (not the web API), which pulls
every artist tagged **hardcore punk**, their release-groups, and band membership. This
requires standing up a separate MusicBrainz database — see
[`backend/README.md`](backend/README.md) for the full procedure.

```bash
cd backend
docker compose run --rm --entrypoint bash hc_archives_back -lc \
  "python -m seed.mb_dump && python -m seed.cover_art"
```

For local development without the dump, seed a small hand-written set of bands
(albums, tracks, members) straight into the app DB instead:

```bash
cd backend
docker compose exec hc_archives_back python -m seed.dev
```

## Development

### Backend (`cd backend`)

```bash
pip install -r requirements-dev.txt
pytest                 # tests (in-memory SQLite, no Postgres needed)
ruff check . --fix     # lint + autofix
ruff format .          # format
```

### Frontend (`cd app`)

```bash
npm run lint           # ESLint
npm run typecheck      # tsc --noEmit
npm run format         # Prettier
```

## Architecture notes

- The backend is the single source of truth for data. The frontend fetches everything
  over HTTP in Server Components / Server Actions; `API_URL` is server-only and never
  shipped to the browser.
- Every backend response is validated against a zod schema at the frontend's network
  boundary (`app/lib/api/client.ts`), mirroring the Pydantic schemas in
  `backend/app/schemas.py`. Changing one means changing the other and the contract doc.
- Reviews and users are out of the current MVP scope.

See [`CLAUDE.md`](CLAUDE.md) for a deeper tour of both codebases.

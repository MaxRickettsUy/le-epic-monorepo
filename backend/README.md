# le-epic-backend

FastAPI + SQLAlchemy backend for a hardcore-punk archive (a genre-scoped
Metal Archives). Postgres for storage; data is seeded from a MusicBrainz
database dump.

## Run the app

```bash
docker compose up --build
```

API on `http://localhost:8000` — interactive docs at `/docs`.

## Seed from the MusicBrainz dump

The catalogue is seeded from a local MusicBrainz Postgres, not the web API.
This pulls every artist tagged **hardcore punk** (globally), their
release-groups, and band membership in a few SQL queries.

1. Stand up a MusicBrainz Postgres with
   [`metabrainz/musicbrainz-docker`](https://github.com/metabrainz/musicbrainz-docker)
   (downloads the twice-weekly dump and imports it — multi-GB, takes a while).
2. Point the seeder at it via `MB_DATABASE_URL` (see `.env.example`); default is
   `postgresql+psycopg2://musicbrainz:musicbrainz@localhost:5433/musicbrainz_db`.
3. Run the seed, then fetch cover art and band art:

   ```bash
   docker compose run --rm --entrypoint bash hc_archives_back -lc \
     "python -m seed.mb_dump && python -m seed.cover_art && python -m seed.band_art && python -m seed.lastfm_tags"
   ```

   - `seed.mb_dump` upserts bands/albums/members by MBID (idempotent — safe to
     re-run after each dump refresh; see Phase 5 in `plans/resurrection.md`).
   - `seed.cover_art` sets `album.art` from the Cover Art Archive for albums that
     have a release-group MBID but no art yet.
   - `seed.band_art` sets `band.band_picture` / `band.logo` from Wikidata
     (`P18` / `P154`) for bands that link to a Wikidata QID via MB. Stores stable
     `commons.wikimedia.org/wiki/Special:FilePath/...` URLs. Idempotent: only
     fills fields that are still null.
   - `seed.lastfm_tags` enriches curated genre coverage from Last.fm for bands
     MB tagged thinly (see `plans/genre-enrichment.md`). Requires
     `LASTFM_API_KEY` in the environment; no-ops with a log line if unset.
     Idempotent; writes `BandGenre` rows tagged `source="lastfm"`.

## Seed lightweight dev data

For local development without the MusicBrainz dump, `seed.dev` inserts a small
set of hand-written hardcore-punk bands (with albums, tracks, and members)
straight into the app DB. It's idempotent by band name — re-running skips bands
that already exist.

```bash
docker compose exec hc_archives_back python -m seed.dev
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests run against in-memory SQLite (no Postgres needed). The seed tests exercise
the real seed SQL against a minimal MusicBrainz-shaped fixture.

## Lint & format

[Ruff](https://docs.astral.sh/ruff/) handles both linting and formatting
(config in `pyproject.toml`):

```bash
ruff check .          # lint
ruff check . --fix    # lint + autofix
ruff format .         # format
```

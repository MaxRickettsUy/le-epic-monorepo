# Resurrection Plan — le-epic-backend

**Project goal:** a hardcore-punk equivalent of Metal Archives. Backend feeds a Next.js frontend at `../le-epic-app`.

**Locked decisions:**
- Genre scope: **hardcore punk** (single genre, not broader punk)
- DB: **Postgres** going forward
- Web framework: **migrate Flask → FastAPI** (async, Pydantic schemas, OpenAPI for free). SQLAlchemy 2.0 stays; Alembic stays.
- MVP scope: **Band + Release only** (no Track seeding for v1)
- Frontend exists and dictates some shape — see "Frontend contract" below

## Where you left off

A Flask + SQLAlchemy backend modeling `Band → Release → Track`, with auth blueprints commented out and seed scripts at the repo root. The API is structured as one Flask blueprint per resource (`app/band`, `app/release`, `app/review`, `app/track`, `app/user`, `app/auth`, `app/tokens`), wired in an app factory in `app/__init__.py`, served by gunicorn (`boot.sh`), using Flask-SQLAlchemy, Flask-Migrate, Flask-Login, and Flask-Cors. **All of this Flask surface gets ported to FastAPI** — see Phase 2. Seeding pulls from MusicBrainz via `musicbrainzngs` at 1 req/sec. There are **five overlapping seed scripts** plus a blocklist generator — each a slightly different evolutionary stage of the same idea. That sprawl is the core symptom of the waste.

## Why the current approach is wasteful

1. **Wide net, filter later.** `seed_bands*.py` searches `tag:*punk* + country:us + artist:a*` (only "a" — never parameterized), then leans on a hand-maintained `data/block_list.json` to throw out false positives like Panic! at the Disco. You pay the MB cost for every wrong band.
2. **N+1 release lookups for one field.** `seed_releases*.py` calls `browse_releases` per band, then `get_release_by_id` for *every* release just to extract `year` — one extra round-trip per release at 1 req/sec.
3. **No caching of MB responses.** Re-running any script re-hits the API. The only dedup is "is this MBID already in the DB?", which happens *after* the call.
4. **Five scripts, overlapping logic.** `seed_bands.py` / `seed_bands_with_blocklist.py` and three release variants duplicate code; the hardcoded `IGNORE_BAND_MBIDS` in `seed_bands.py:22-35` is dead weight now that the blocklist exists.
5. **Querying releases instead of release-groups.** A "release-group" is the album; "releases" are pressings/reissues. You want one row per album, not per pressing. `generate_blocklist_from_releases.py` already uses `browse_release_groups` — the seeders should too.

## The cheaper architecture: MusicBrainz data dump

**The unlock:** MusicBrainz publishes a full database dump (free, refreshed twice weekly, official `metabrainz/musicbrainz-docker` image to stand it up locally as Postgres).

For a genre-scoped seed this is dramatically faster and cheaper than the web API:
- One SQL query gets every artist tagged `hardcore punk` with their release-groups
- No rate limit, no N+1, no blocklist needed (tag filter happens at query time)
- Run takes minutes, not days

The web API becomes a **fill-in tool** for things the dump doesn't have (cover art via Cover Art Archive, brand-new releases since the last dump, user-initiated single-band imports).

## Frontend contract (from `../le-epic-app/lib/types.ts`)

The frontend already expects a shape the backend partly delivers:

| Field | Backend has it? | Notes |
|---|---|---|
| `Band.name, country, location, status, label, band_picture` | ✅ | |
| `Band.members[]` (name, role) | ❌ | **Missing entirely.** Need a `Member` table + relationship. MB dump has this (`artist_credit`, band membership relations). |
| `Band.releases[]` | ✅ | via FK |
| `Release.name, year, label, art, release_type, length` | ✅ | `art` field exists but never populated by current seeders |
| `Release.avg_review, review_count` | ❌ | Derived field; needs a computed column or view |
| `Release.band` (nested object) | ✅ | via FK |

**Action implied:** schema gains a `Member` (or `BandMember`) table in Phase 3, and the seeding query needs to pull membership from the dump.

## Phased plan

### Phase 1 — Boot it on Postgres (½ day, no logic changes)

**Still on Flask in this phase** — the framework swap is the very next phase (Phase 2). Goal here is only: app runs against Postgres, frontend wiring confirmed, before we touch the web layer.
- Switch `config.py` default and `docker-compose.yml` from MySQL/SQLite to **Postgres**
- Delete the SQLite `app.db` and the MySQL service from compose
- Re-run migrations against fresh Postgres; confirm the app boots
- Confirm frontend can hit `/band` and `/release` endpoints (empty responses are fine — just verify wiring)
- Decide: keep the half-commented auth blueprints in `app/__init__.py` or delete them outright. (Recommend: delete for MVP; reviews don't need users yet, or stub a single dev user.)

### Phase 2 — Migrate Flask → FastAPI (the framework swap)

Done **before** reseeding and schema cleanup so everything built afterward is FastAPI-native and we never port the web layer twice. The data layer (SQLAlchemy 2.0 models + Alembic migrations) is **kept as-is**; only the web layer is rewritten. Tradeoff to accept: the Pydantic response schemas written here get revised in Phase 3 when the schema changes (Member table, `Release`→`Album` rename) — that's cheaper than re-porting all the routes.

- **Dependencies:** drop `Flask`, `Flask-Cors`, `Flask-Login`, `Flask-Migrate`, `Flask-SQLAlchemy`, `gunicorn`, `Werkzeug`. Add `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `python-jose[cryptography]` + `passlib[bcrypt]` (only if auth stays). Keep `alembic`, `SQLAlchemy`, `musicbrainzngs`, `python-dotenv`. Pin everything.
- **DB session:** replace Flask-SQLAlchemy's `db.session` with a plain SQLAlchemy 2.0 `sessionmaker` + a FastAPI dependency (`get_db`) that yields a session per request. Models stop subclassing `db.Model` and use a plain `DeclarativeBase`.
- **Migrations:** Flask-Migrate is just an Alembic wrapper — switch `migrations/env.py` to import the SQLAlchemy `Base.metadata` directly instead of via the Flask app. Existing migration history is preserved (no schema reset).
- **Routes → routers:** convert each Flask blueprint to an `APIRouter` (`app/band`, `app/release`, etc.). Mount them on a single `FastAPI()` app in `app/__init__.py` (replaces the app factory).
- **Schemas:** define Pydantic models matching the **frontend contract** (`../le-epic-app/lib/types.ts`) as response models — this also gives typed OpenAPI docs at `/docs` for free.
- **CORS:** Flask-Cors → FastAPI `CORSMiddleware`.
- **Config:** `config.py` → `pydantic-settings` `BaseSettings`; retire `.flaskenv`.
- **Serving:** `boot.sh`/`Dockerfile` swap `gunicorn ... hc_archives_back:app` for `uvicorn app:app` (or gunicorn with the uvicorn worker class). `flask db upgrade` → `alembic upgrade head`.
- **Auth:** if reviews/auth stay (see open question 1), reimplement Flask-Login session auth as FastAPI dependency-injected JWT/OAuth2 (`OAuth2PasswordBearer`). If reviews are out of MVP, delete the `auth`, `tokens`, `user`, and `review` modules entirely instead of porting them.
- Split `tests.py` (27KB at root) into a `tests/` package and rewrite against FastAPI's `TestClient`.
- Add a `services/` layer so MB fetching and review aggregation aren't done inline in routers.

### Phase 3 — Schema cleanup ✅ DONE (2026-05-21)

Done on FastAPI; reflected in SQLAlchemy models, Alembic migration `c1d2e3f4a5b6` (reversible — upgrade/downgrade tested), and the Pydantic schemas.
- ✅ Added `Member` table + `band_member` association (carries `role`); `BandDetail.members` now populated. No member write endpoint yet — membership arrives via the Phase 4 seed.
- ✅ Added `created_at` / `updated_at` (timezone-aware, server-default `now()`) to band, album, track, member, band_member.
- ✅ **Release → Album, internal only** (decided): table/model renamed to `album`, `mbid` → `release_group_mbid` (one row per release-group). API stays `/release` and JSON keys unchanged so the frontend is untouched (model attributes `releases`/`release`/`release_id` preserved).
- ✅ Added DB-level `ON DELETE CASCADE` to band→album, album→track, band_member FKs (deferred from Phase 2); relationships use `passive_deletes=True`.
- ✅ **Kept `Track`** (decided): frontend release page has a Tracks tab reading `release.tracks`. Revisit dropping later if truly unused.
- ✅ `avg_review` / `review_count`: resolved as constant `0` at query time — reviews are out of MVP so there's nothing to aggregate; no Postgres view needed.
- ✅ Dropped legacy `review` / `user` tables (orphaned since Phase 2).
- ⏭️ `Band.location` vs `country` overlap: left as-is for now; MB dump has structured area data, revisit during Phase 4 seeding.

### Phase 4 — Reseed from the MB dump (the core fix) ✅ DONE (2026-05-21)

Seed scripts are framework-agnostic, so this landed cleanly after the FastAPI swap and the final schema.
- ✅ `seed/mb_dump.py` — one seeder: connects to the MB Postgres (`MB_DATABASE_URL`), queries artists tagged `hardcore punk` **globally** → release-groups (uses `release_group_meta.first_release_date_year`, no N+1) → area for location/country → `l_artist_artist` membership into `Member`/`band_member`. Upserts by MBID, idempotent, logs counts. No blocklist.
- ✅ `seed/cover_art.py` — separate step: reads albums with a release-group MBID and null art, hits the Cover Art Archive `release-group/{mbid}/front` endpoint, sets `album.art`.
- ✅ Added `mb_database_url` + `seed_tag` settings; README documents standing up `metabrainz/musicbrainz-docker` and running the seed.
- ✅ **Deleted** all six legacy `seed_*.py`, `generate_blocklist_from_releases.py`, `data/block_list.json` (and the now-dead `/app/data` volume).
- ✅ Verified with a minimal MusicBrainz-shaped SQLite fixture (`tests/test_seed.py`): global bands seeded / off-genre excluded / albums + members + roles correct / idempotent re-run / selective cover art. **19 tests pass.**
- ⚠️ **Operational note:** the full ~100GB+ dump import (`musicbrainz-docker`) was *not* run in this environment — that's a one-time host step. The seeder is verified against the fixture; the real run is `python -m seed.mb_dump` once the MB Postgres is up.
- `Band.location` vs `country`: still set to the same area name for now; refine with the dump's structured area hierarchy when needed.

### Phase 5 — Ongoing data refresh

- Cron the MB dump re-import weekly (the dump cycle); diff against existing rows by MBID, only update changed
- Use the web API only for: brand-new releases since last dump, cover art, user-initiated band adds

## Open questions still worth answering

1. ~~**Reviews in MVP or not?**~~ **DECIDED (2026-05-21): reviews are OUT of MVP.** Drop the `auth`/`tokens`/`user`/`review` modules entirely; no FastAPI auth needed. Frontend's `avg_review` / `review_count` fields return `0` / `null`. (Auth/JWT can be re-added cleanly post-MVP.)
2. ~~**Geographic scope?**~~ **DECIDED (2026-05-21): global** — no country filter, every artist tagged `hardcore punk` worldwide.
3. ~~**Cover art priority?**~~ **DECIDED (2026-05-21): yes, fetch in Phase 4** — a separate Cover Art Archive step populates `album.art` after the dump seed.

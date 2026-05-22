# Resurrection Plan — le-epic-backend

**Project goal:** a hardcore-punk equivalent of Metal Archives. Backend feeds a Next.js frontend at `../le-epic-app`.

**Locked decisions:**
- Genre scope: **hardcore punk** (single genre, not broader punk)
- DB: **Postgres** going forward
- MVP scope: **Band + Release only** (no Track seeding for v1)
- Frontend exists and dictates some shape — see "Frontend contract" below

## Where you left off

A Flask + SQLAlchemy backend modeling `Band → Release → Track`, with auth blueprints commented out and seed scripts at the repo root. Seeding pulls from MusicBrainz via `musicbrainzngs` at 1 req/sec. There are **five overlapping seed scripts** plus a blocklist generator — each a slightly different evolutionary stage of the same idea. That sprawl is the core symptom of the waste.

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
- Switch `config.py` default and `docker-compose.yml` from MySQL/SQLite to **Postgres**
- Delete the SQLite `app.db` and the MySQL service from compose
- Re-run migrations against fresh Postgres; confirm the app boots
- Confirm frontend can hit `/band` and `/release` endpoints (empty responses are fine — just verify wiring)
- Decide: keep the half-commented auth blueprints in `app/__init__.py` or delete them outright. (Recommend: delete for MVP; reviews don't need users yet, or stub a single dev user.)

### Phase 2 — Reseed from the MB dump (the core fix)
- Stand up `metabrainz/musicbrainz-docker` alongside the app's Postgres as a separate DB
- Write **one** seed script (`seed_from_mb_dump.py`) that:
  1. Connects to the MB Postgres
  2. Runs a single query: artists with tag `hardcore punk` → join release-groups → join first-release-date for year → join area for country/location
  3. Bulk-inserts into the app DB in one transaction, upserting by MBID
  4. Logs what it did (counts, skips) but does not need a blocklist
- Use `release_group.first_release_date_year` directly (kills the N+1)
- **Delete** all five existing seed scripts, `generate_blocklist_from_releases.py`, and `data/block_list.json` — obsolete
- Leave `musicbrainzngs` in `requirements.txt` only for the cover-art fetch step (separate small script that reads bands from app DB and hits Cover Art Archive for `Release.art`)

### Phase 3 — Schema cleanup
- Add `Member` table + `BandMember` join (frontend already expects this)
- Add `created_at` / `updated_at` everywhere (currently missing)
- Decide on the release-vs-release-group question: rename `Release` → `Album` and store the **release-group MBID** instead of release MBID (one row per album, not per pressing). Frontend uses `release_type` and `year` — both available at release-group level.
- Reconsider `Band.location` vs `country` overlap; MB dump has structured area data
- Drop the `Track` table and `track` blueprint for now (MVP is Band + Release only) — keep the migration history but stop maintaining the code. Or just delete; can re-add cleanly later.
- Add `avg_review` / `review_count` either as a Postgres view, a generated column, or computed at query time

### Phase 4 — App refactor
- Bump dependencies; Flask 3.0.3 / SQLAlchemy 2.0 are fine, but pin versions
- Split `tests.py` (27KB at root) into a `tests/` package
- Add a `services/` layer so MB fetching and review aggregation aren't done inline
- Decide review/auth story: either re-enable auth blueprints or admit reviews are out of MVP and remove them too

### Phase 5 — Ongoing data refresh
- Cron the MB dump re-import weekly (the dump cycle); diff against existing rows by MBID, only update changed
- Use the web API only for: brand-new releases since last dump, cover art, user-initiated band adds

## Open questions still worth answering before Phase 2

1. **Reviews in MVP or not?** If yes, auth has to come back. If no, drop the `Review` model and blueprint and the frontend's review fields can return `0` / `null`.
2. **Geographic scope?** Current seeders filter `country:us`. Keep US-only for MVP, or global from the start? The dump makes global cheap.
3. **Cover art priority?** Phase 2 leaves `Release.art` empty. Acceptable for first browse, or do you want the Cover Art Archive pull in Phase 2?

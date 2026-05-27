# Sub-genre Plan — le-epic-backend

**Goal:** attach a controlled set of hardcore sub-genres (NYHC, youth crew, melodic
hardcore, …) to bands, sourced from MusicBrainz tags but mapped onto a **curated
vocabulary we own**. Surface them on band pages, as a search facet, and as a similarity
signal.

**Context:** the site is genre-scoped to **hardcore punk** (see `resurrection.md`). The
seed (`seed/mb_dump.py`) already selects artists via MusicBrainz's `artist_tag`/`tag`
tables (`WHERE t.name = 'hardcore punk'`) but uses the tag purely as a scope *filter* and
persists none of the other tags. The DB has **no genre column** today.

## Locked decisions
- **Curated vocabulary, not raw MB tags.** MB `artist_tag` is free-form and noisy
  (misspellings, joke tags, one-vote outliers, out-of-scope genres). We own a canonical
  list + an alias layer so MB variants (`nyhc` / `new york hardcore` / `n.y.h.c.`)
  collapse to one genre.
- **Vocabulary source of truth lives in code** (`app/genres.py`), not the DB. The
  `genre` table is a seeded, queryable cache of that constant — not a second source.
- **Bands only (v1).** No album-level genres: MB tags releases separately and most album
  tags duplicate the band's.
- **Model mirrors `BandMember`** — a `genre` table + `band_genre` association, carrying
  MB `vote_count` so we can later rank a band's "primary" genre and order facets without
  re-seeding.

## Open questions
1. **Final curated list.** Step 1 ships a ~10-entry draft (below); extend/lock before the
   seed step (step 2) populates anything.
2. **MB dump availability.** Steps 1, 3, 4, 5 need no MB access. Step 2 (populate) needs
   the MusicBrainz dump Postgres (port 5433, `mb_database_url`) running — same
   prerequisite as the existing seed. If unavailable, schema + API + UI still ship; only
   auto-population waits.

## Phased plan (each step independently shippable)

### Step 1 — Model + migration + curated vocabulary  ✅ DONE (2026-05-26)
- `app/genres.py`: `CURATED_GENRES` mapping `slug -> (display name, {lowercased MB tag
  aliases})`, plus a derived `ALIAS_TO_SLUG` lookup.
- `app/models.py`: `Genre(slug unique, name)` + `BandGenre(band_id, genre_id, vote_count)`
  association, mirroring `BandMember`. `Band.genres` relationship; `slug`/`name`
  convenience properties on `BandGenre` so a `{slug, name}` schema validates off the link.
- Alembic autogenerate revision creating `genre` + `band_genre` (reversible; `boot.sh`
  runs `upgrade head` on start). Draft list below — empty tables until step 2.
- Tests: alias map (variants collapse to one slug; non-curated ignored), and that the new
  tables/relationships round-trip.

### Step 2 — Seed  ✅ DONE (2026-05-26), pending a real MB-dump run
- ✅ `_ARTIST_TAGS_SQL` over `artist_tag`/`tag`: `(artist_id, tag_name, count AS votes)`
  for in-scope artist ids — same tables the scope filter already uses.
- ✅ New seed step after members: upsert curated `genre` rows from `CURATED_GENRES`
  (idempotent by slug); for each `(artist, tag, votes)`, `slug_for_tag()`, skip if not
  curated (incl. the broad scope tag), upsert `BandGenre`. Duplicate aliases of the same
  genre keep the strongest vote (max).
- ✅ Extended `SeedStats` (`genres_linked` / `genre_links_updated`).
- ✅ Verified against the SQLite MB fixture in `tests/test_seed.py`: alias collapsing,
  non-curated tags dropped, bands with no sub-genre, idempotent re-run. **30 tests pass.**
- ⚠️ Like Phase 4 in `resurrection.md`, the real run (`python -m seed.mb_dump` against the
  ~100GB MB Postgres on port 5433) was **not** executed here — that's the one-time host
  step that actually populates existing bands.

### Step 3 — API + contract + zod
- `app/schemas.py`: `GenreOut {slug, name}`; add `genres: list[GenreOut] = []` to
  `BandBase` (appears on list items + detail). Eager-load `Band.genres→genre` in the band
  routes' `selectinload`.
- Mirror in `app/lib/schemas/index.ts` (zod) + update `app/docs/api-contract.md` (the
  established change-backend-schema → update-zod+contract loop).

### Step 4 — Frontend display
- Band detail (`TopSection`): genre badges (`components/ui/badge.tsx`) under the name.
- `BandCard`: optional top 1–2 genres. Search results rows: genre badges.

### Step 5 — Search facet + similarity factor
- Extend `/search` with optional `?genre=<slug>` filter (join `band_genre`); optionally
  fold genre-name matches into the band `OR`.
- Add `"shared_genre"` to `SIMILARITY_WEIGHTS` in `band/routes.py` — count shared genres
  via the same subquery shape as `shared_members`; expose in `SimilarBand` "why" fields.

## Draft curated list (step 1; not yet locked — see open question 1)
nyhc, youth-crew, melodic-hardcore, beatdown, powerviolence, metalcore, post-hardcore,
d-beat, crust, straight-edge. Aliases captured in `app/genres.py`.

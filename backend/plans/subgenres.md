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

### Step 3 — API + contract + zod  ✅ DONE (2026-05-27)
- ✅ `app/schemas.py`: `GenreOut {slug, name}`; `genres: list[GenreOut] = []` on `BandBase`
  (so it appears on list items + detail). `Band.genres` relationship now `order_by`
  `vote_count` desc, so the primary sub-genre serializes first (deterministic for tests).
- ✅ Eager-load `Band.genres→genre` via `selectinload` in both band routes (`get_all` list
  + `get` detail).
- ✅ Mirrored in `app/lib/schemas/index.ts` (`genreSchema`, `genres` on `bandBaseSchema`,
  `Genre` type) + updated `app/docs/api-contract.md` (`Genre` shape, `BandBase` field,
  detail eager-load note).
- ✅ Tests in `tests/test_genres.py`: genres on detail ordered by votes, on list items,
  and `[]` when a band has none. **41 tests pass.**

### Step 4 — Frontend display  ✅ DONE (2026-05-27)
- ✅ Reusable `components/GenreBadges.tsx` (strongest-voted first; optional `limit`;
  renders nothing when empty) wraps `components/ui/badge.tsx` (`secondary` variant).
- ✅ Band detail (`TopSection`): badges under the name (band page passes `band.genres`).
- ✅ `BandCard`: top 2 genres (`limit={2}`) under the location.
- ✅ Search band rows: badges beside the name. Required adding `genres` to
  `BandSearchItem` (schemas.py + zod + contract) and a `selectinload` in the search route,
  since search rows previously carried no genres.
- ✅ Tests: search rows carry genres ordered by votes, and default to `[]`. **43 backend
  tests pass; frontend typecheck + lint clean.**

### Step 5 — Search facet + similarity factor  ✅ DONE (2026-05-27)
- ✅ `/search` takes optional `?genre=<slug>`: bands restricted to that curated slug via
  `Band.genres.any(BandGenre.genre.has(Genre.slug == ...))`. Also folded genre-name
  matches into the band text `OR`, so `?q=youth` matches a youth-crew band by genre.
- ✅ Added `"shared_genre": 3` to `SIMILARITY_WEIGHTS` (between location and label); count
  shared genres with the same correlated-subquery shape as `shared_members`. Exposed as
  `shared_genres` on `SimilarBand` (schema + zod + contract) and rendered in the "why"
  badges (`similar.tsx`).
- ✅ Tests: shared-genre scoring (`test_band.py`), genre facet restricts results + unknown
  slug empty + genre-name text match (`test_search.py`). **46 backend tests pass;
  frontend typecheck + lint + prettier clean.**

## Status: all five steps complete. Remaining one-time host work is the real
`python -m seed.mb_dump` run against the MB Postgres (step 2 ⚠️), which populates
genres on existing bands; until then the tables are empty and the UI degrades to
no badges / empty facet, by design.

## Draft curated list (step 1; not yet locked — see open question 1)
nyhc, youth-crew, melodic-hardcore, beatdown, powerviolence, metalcore, post-hardcore,
d-beat, crust, straight-edge. Aliases captured in `app/genres.py`.

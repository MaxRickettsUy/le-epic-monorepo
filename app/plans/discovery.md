# Discovery Plan — le-epic

**Goal:** make the catalogue _browsable_, not just searchable. Today you can only reach
a band by knowing its name (search) or by it landing in the 10-item "Recently added" row.
Modelled on Metal Archives (browse by genre / country / alphabetical) and Album of the
Year (rich release pages, a discovery-oriented home), kept **read-only** — no user
content (reviews, ratings, lists, lineups) in this scope.

**Context:** the frontend is server-first (Server Components fetch directly from the
backend; no client-side app-data fetching). Every response is zod-validated at the
`lib/api/client.ts` boundary and mirrored in `app/docs/api-contract.md`. The curated
sub-genre vocabulary already exists (`backend/app/genres.py` → `genre` / `band_genre`
tables; see `backend/plans/subgenres.md`) and `/search` already accepts a `?genre=<slug>`
facet — we extend that work rather than introduce new data modelling.

## Locked decisions

- **Faceted band index, not a multi-page browse hub.** One `/bands` page with filters
  (genre, country, A–Z) + sort + pagination, driven entirely by URL search params
  (server-first, no client fetching). One extended endpoint, one new route.
- **New read-only endpoints are fine.** This scope adds GET endpoints only; no writes,
  no new tables, no schema migrations. All filtering rides existing columns/relationships.
- **Genre vocabulary stays code-owned.** A genre-list endpoint serves
  `CURATED_GENRES` from `app/genres.py` directly, so genre navigation works even before
  the MB seed populates `band_genre` (degrades to an empty result set, never an error).
- **No user data.** Reviews/ratings/lineups stay out (members are always `[]`). Anything
  AOTY-like that needs scores is explicitly deferred.

## Open questions

1. **Country data quality.** `band.country` / `band.location` are free-text (not
   normalized). "Browse by country" does `SELECT DISTINCT country` — values may be messy
   (`"USA"` vs `"United States"`). Acceptable for v1? If not, normalization is a separate
   pre-req. Phase 1 ships genre + A–Z regardless; country is the one facet exposed to this risk.
2. **Empty `band_genre`.** Until the one-time `python -m seed.mb_dump` run populates
   genres (subgenres.md step 2 ⚠️), the genre facet and genre nav return nothing. By
   design — the UI degrades to no badges / empty results. Worth confirming that's
   acceptable for a demo before then.

## Recommended sequencing

**Phase 2 first** (release enrichment — pure frontend, fully independent, quick win) →
**Phase 1** (the faceted index + `/genre` endpoint — the foundation the rest leans on) →
**Phase 4** (clickable genres — cheap, just needs Phase 1's `/bands?genre=` target) →
**Phase 3** (landing discovery — reuses Phase 1's endpoints + Phase 4's genre links).

---

## Phase 1 — Faceted band index (point 1: browse / discovery)

The foundation. A `/bands` page that lists the whole catalogue with genre / country /
alphabetical filters, sort, and real pagination (the backend already paginates; nothing
in the UI exposes it today).

### Backend (`cd backend`)

- **Extend `GET /band/`** (`app/band/routes.py::get_all`) with optional query params,
  all combinable:
  - `genre: str | None` — restrict to a curated slug via
    `Band.genres.any(BandGenre.genre.has(Genre.slug == genre))` (the exact pattern already
    in `app/search/routes.py`).
  - `country: str | None` — exact match on `Band.country`.
  - `letter: str | None` — `Band.name.ilike(f"{letter}%")` (escape LIKE wildcards as
    `search/routes.py::_contains` does); reserve `#` for names not starting A–Z
    (`~ Band.name.op("~")('^[A-Za-z]')` or a `NOT ilike any(letter)` fallback). Validate
    single char.
  - keep existing `page` + `sort`.
  - **Fix the count:** `total` is currently an unconditional `count(Band)`. Build the
    filter list once and apply it to **both** the count and the select, or `has_next`
    breaks under filters. (Small refactor — collect `filters: list` and `.where(*filters)`.)
- **New `GET /genre/`** — small new router `app/genre/routes.py` mounted at `/genre` in
  `app/__init__.py`, returning `list[GenreOut]` straight from `CURATED_GENRES` (sorted by
  display name). No DB hit; always available. (`GenreOut {slug, name}` already exists in
  `schemas.py` from subgenres step 3.)
- **New `GET /band/countries`** — `SELECT country, COUNT(*) GROUP BY country ORDER BY
count DESC, country` → `list[{country: str, count: int}]` (new `CountryCount` schema) to
  populate the country filter. (Skip/defer if open question 1 rules country out for v1.)
- **Contract + tests:** document the new params/endpoints in `app/docs/api-contract.md`;
  tests in `tests/test_band.py` for each facet, combined facets, count/pagination under
  filter, unknown slug → empty, `letter=#`; new `tests/test_genre.py` for the genre list.

### Frontend (`cd app`)

- **`lib/api/bands.ts`:** widen `listBands` to take a `filters` object
  (`{ page, sort, genre?, country?, letter? }`) and build the query string; add
  `listGenres()` (→ `/genre/`, new `genreListSchema`) and `listCountries()`
  (→ `/band/countries`). Mirror new schemas in `lib/schemas/index.ts`, re-export types.
- **New route `app/bands/page.tsx`** (Server Component, `dynamic = "force-dynamic"`):
  reads `searchParams` (`page`, `sort`, `genre`, `country`, `letter`), fetches the
  filtered list + genre/country options, renders the existing `BandCard` grid (same
  markup as `app/page.tsx`).
- **Filter controls (all URL-driven, no client state):**
  - A–Z bar: a row of `Link`s setting `?letter=`.
  - Genre + country: either `<form method="get">` `<select>`s (server-submit) or chip
    `Link`s — match whichever the codebase prefers; genre chips can reuse Phase 4's
    linked `GenreBadges`.
  - Sort toggle: `Link`s for name/recent.
- **New `components/Pagination.tsx`:** Prev/Next from `BandList.next`/`prev`, preserving
  the other search params. Reusable by Phase 3.
- **`components/ui/header.tsx`:** add a "Browse" `Link` to `/bands`.
- **Verify:** `npm run typecheck` + `lint`; load `/bands` and exercise each facet +
  pagination in the browser.

---

## Phase 2 — Release page enrichment (point 2) · frontend-only

`ReleaseDetail` already returns `release_type`/`type`, `year`, `label`, `length`, `art`,
plus the nested `band` and sorted `tracks` — the page (`app/release/[id]/page.tsx`) shows
only the band name, art, and a tracklist. No backend change; just render what we already
have.

- **Release header:** the page reuses the band `TopSection` (passing band name + art),
  which is band-shaped (shows "Edit Band" / "Add Release", "Years active"). Build a
  small release-specific header instead (or parameterize `TopSection`) showing: **album
  title**, **year**, **release type** (LP/EP/demo — `type`), **label**, **total runtime**,
  and a link back to the band. Keep the cover art prominent.
- **Runtime:** use `release.length` when present; otherwise sum `track.length`. Reuse the
  `formatLength` helper already in `app/release/[id]/table.tsx` (lift it to a shared
  `lib/format.ts` so the header and table share it).
- **Keep the tracks tab** as-is.
- **Verify:** typecheck/lint; check a release with full metadata and one with most fields
  null (graceful omission, no empty labels).

---

## Phase 3 — Landing-page discovery (point 3)

Make `/` a discovery surface, not a single recent-bands row. Depends on Phase 1's
`/genre` endpoint and Phase 4's genre links.

### Backend (`cd backend`)

- **New `GET /release/`** (`app/release/routes.py`) mirroring `get_all` for bands:
  `page` + `sort` (`recent` = `created_at desc`, or `year desc`; pick one and document),
  `joinedload(Album.band)` for the band name/link. Response `ReleaseList`
  (`{ releases: ReleaseListItem[], next, prev }`) where `ReleaseListItem` ≈
  `AlbumSearchItem` (`id, name, year, art, band_id, band_name`). New schemas + contract +
  `tests/test_release.py` (recent ordering, pagination, band eager-load).

### Frontend (`cd app`)

- **`lib/api/releases.ts`:** add `listReleases({ page, sort })` + `releaseListSchema`.
- **`app/page.tsx`** sections:
  - "Recently added bands" (existing grid).
  - **"Recent releases"** — a grid of album tiles. Extract a `components/AlbumCard.tsx`
    (art + initial fallback, album name, band name + year), reusing `BandCard`'s shape.
  - **"Browse by genre"** — chips linking to `/bands?genre=<slug>` (from `/genre/`),
    i.e. Phase 4's linked badges; doubles as the entry point into Phase 1.
- **Verify:** typecheck/lint; load `/` and click through a genre chip → `/bands?genre=`,
  an album tile → `/release/{id}`.

---

## Phase 4 — Genres as navigation (point 4) · frontend-only, depends on Phase 1

Genres are display-only badges today. Make them links into the faceted index so a genre
is a way to _navigate_, everywhere it appears.

- **`components/GenreBadges.tsx`:** wrap each `Badge` in a `Link` to
  `/bands?genre=${g.slug}`. Default to linked; if any non-navigational usage turns up
  (e.g. inside a form), add an opt-out `asLinks={false}` prop — otherwise keep it simple.
- **Propagates for free** to every consumer: `BandCard`, band detail `TopSection`, and
  search band rows (`app/search/page.tsx`) all render `GenreBadges` already.
- **Requires Phase 1** (`/bands?genre=` must exist) — ship after it.
- **Verify:** typecheck/lint; click a genre badge on a band page / search result → lands
  on the filtered `/bands` list.

---

## Status: not started — planning only.

All four phases are independently shippable; Phase 2 has no dependencies, Phases 3 and 4
depend on Phase 1's `/genre` endpoint and `/bands` route. No migrations, no writes, no
user data in scope. The genre facet/nav is live only after the one-time MB seed populates
`band_genre` (subgenres.md step 2 ⚠️).

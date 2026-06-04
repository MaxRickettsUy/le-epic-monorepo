# Genre Enrichment Plan — le-epic-backend

**Problem:** MusicBrainz's `artist_tag` coverage is thin for popular 2010s bands —
they're often untagged, or not tagged as hardcore/sub-genres at all. The MB dump
is a clean **entity backbone** (stable MBIDs the whole pipeline keys off) but a
poor **genre signal** for newer artists. We layer a tag-enrichment pass on top of
the existing seed rather than switching data sources.

**Strategy (locked):** Keep MusicBrainz as the entity backbone. Add a separate,
MBID-keyed enrichment pass that fetches tags from Last.fm (and optionally Discogs),
funnels them through the *same* `slug_for_tag` → `BandGenre` chokepoint the MB seed
uses, and writes links tagged with `source="lastfm"`. Enrichment never invents
entities — it only adds genre links to bands MB already seeded.

## Phase 0 — Plumbing (DONE)

The model is ready to receive enrichment data; this shipped on
`feat/auto-flag-allowlist`:

- **`BandGenre.source`** column (`"mb"` default / `"lastfm"` / …) — migration
  `e7a8b9c0d1e2`. Records link provenance. Internal only; wire shape (`GenreOut`
  is `{slug, name}`) unchanged, so no api-contract change.
- **`seed.genre_allowlist.decide_auto_flag(...)`** — the off-genre verdict, with a
  `has_enrichment_core` escape hatch. A band MB only tagged with the seed tag (would
  be flagged) is **rescued** when it carries a non-`mb` curated link.
- **`seed.mb_dump`** writes MB links with `source="mb"`, and before the audit loop
  queries which bands have a non-`mb` link, passing that into `decide_auto_flag`.
  Enrichment links survive an MB re-seed (only non-positive-vote rows are purged),
  so an enriched band **stays unflagged on every subsequent run** — re-seeding
  never clobbers the enrichment verdict.
- Tests: unit coverage for `decide_auto_flag` (all branches) + an integration test
  proving a `lastfm` link rescues a band across re-seeds.

## Phase 1 — Last.fm tag fetcher (NEXT)

A new standalone seeder, run *after* `seed.mb_dump` (it depends on bands already
existing with MBIDs):

```
python -m seed.mb_dump        # entities + MB tags   (unchanged)
python -m seed.lastfm_tags    # enrich genres        (new)
```

**Why a separate script, not folded into `run_seed`:** `mb_dump` talks only to the
local MB Postgres — offline, fast, idempotent. Last.fm is a rate-limited web API
(the same cost profile this project deliberately moved *away* from with the dump).
Keeping it separate means a flaky network pass can't wedge the core entity seed,
and enrichment can be re-run without re-importing the dump.

### Steps

1. **Settings** (`app/settings.py`): add `lastfm_api_key: str | None` and
   `lastfm_api_url` (default `https://ws.audioscrobbler.com/2.0/`), pydantic-settings
   from env/`.env`. The fetcher no-ops with a clear log line if the key is unset.
2. **Service** (`app/services/lastfm.py`, mirroring `services/musicbrainz.py`):
   isolate all Last.fm HTTP here. One function:
   `top_tags(mbid: str) -> list[tuple[str, int]]` calling
   `?method=artist.getTopTags&mbid=<mbid>&format=json`. Returns `(name, weight)`
   pairs (weight 0–100). Inject the HTTP client / a `fetch` callable so tests pass a
   fake (same pattern as `band_art.fetch_band_art(resolve=...)`).
3. **Seeder** (`seed/lastfm_tags.py`):
   - Iterate `Band` rows with `mbid is not null`.
   - For each: `top_tags(mbid)` → for each `(name, weight)`, `slug_for_tag(name)`;
     drop non-curated (filters Last.fm noise like "seen live", "favorite" for free).
   - **Upsert `BandGenre(..., source="lastfm")`** keyed by `(band_id, genre_id)`.
     Idempotent by that key, exactly like the MB genre loop.
   - **vote_count normalization:** Last.fm weight is 0–100; MB votes are small
     integers (single digits typical). Don't store raw 100s — they'd dominate the
     `order_by(desc(vote_count))` primary-genre sort and swamp real MB votes. Decide
     a scale (open question below) and apply it consistently.
   - Conflict rule when a `(band, genre)` link already exists from MB: keep the
     stronger signal, but **don't flip `source`** — an MB-originated link stays
     `"mb"`. Only create `"lastfm"` rows for genres MB didn't already link.
   - Rate-limit politely (Last.fm allows ~5 req/s; throttle + retry on 429).
4. **Re-flag after enrichment:** the rescue only takes effect on the *next*
   `mb_dump` run (that's where `auto_flagged` is computed). Either (a) document that
   ordering and rely on it, or (b) have `lastfm_tags` recompute `auto_flagged` for
   bands it touched via `decide_auto_flag` so the flag clears in the same pass.
   **Lean (b)** — a one-source-of-truth helper already exists; call it with the
   freshly-known `has_enrichment_core=True` and the band's stored `mb_tags`.
5. **Tests** (`tests/test_seed_lastfm.py`): fake `top_tags`, assert curated tags
   become `source="lastfm"` links, noise is dropped, normalization is applied,
   re-run is idempotent, and (if 4b) a rescued band's `auto_flagged` clears in-pass.
6. **Docs:** add the run step to `backend/README.md` (after `cover_art`), note the
   `LASTFM_API_KEY` env var, and a line in `plans/resurrection.md` cross-referencing
   this plan. No `api-contract.md` change (wire shape unchanged).

## Open questions (decide before/at Phase 1)

- **vote_count scale.** Options: (a) bucket Last.fm 0–100 into a small fixed range
  (e.g. `round(weight / 20)` → 0–5) so it sits alongside MB vote magnitudes;
  (b) store raw but sort by `(source priority, vote_count)` so MB always ranks first.
  Leaning (a) — simpler, keeps one sort key.
- **Should enrichment-only genres show on the public band page,** or only count
  toward the auto-flag rescue (internal)? If shown, a band could display a genre no
  MB user ever voted. Probably fine and desirable (that's the coverage win), but
  confirm with the curator surface before launch.
- **Provider weight threshold.** Last.fm returns a long noisy tail; only map tags
  above some weight (e.g. ≥ 10) to avoid one stray "metalcore" vote rescuing a band.

## Phase 2 — Discogs styles (OPTIONAL, later)

Discogs has excellent punk/hardcore *style* granularity but messier identity (no
MBID; match via the Discogs URL MB already stores in `l_artist_url`, or by name as
a last resort). Same funnel, `source="discogs"`. Only pursue if Last.fm coverage
proves insufficient after Phase 1 — don't build two providers speculatively.

## Invariants to preserve

- MBID stays the join key end-to-end; enrichment never creates `Band`/`Album` rows.
- All genre signal goes through `app.genres.slug_for_tag` — no provider gets its own
  genre vocabulary.
- `decide_auto_flag` is the single source of the off-genre verdict; don't re-inline
  the rule in the new seeder.
- Enrichment links must survive an MB re-seed (they already do — keep their
  `vote_count` positive so the non-positive purge doesn't catch them).

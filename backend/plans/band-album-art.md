# Band & album art

Pull cover art and band art into the seeded catalogue. The frontend already
renders all three fields (`album.art`, `band.band_picture`, `band.logo`); only
the backfill seeds need to run end-to-end.

## State at hand-off

- App DB seeded from MB dump: 2,262 bands, 13,138 albums, 2,603 members.
- `album.art`, `band.band_picture`, `band.logo` all null — neither art seed has
  committed yet.
- `seed/cover_art.py` exists and works (pre-existing).
- `seed/band_art.py` exists on disk but is **not** in the running
  `hc_archives_back` image (the image was built before the file existed).
- MB mirror is up on host port 5433
  (`musicbrainz-docker-db-1`, db = `musicbrainz_db`, schema = `musicbrainz`).
- `backend/.env` has `MB_DATABASE_URL` pointing the seed at it via
  `host.docker.internal:5433` with `search_path=musicbrainz,public`.
- Frontend `next.config.mjs` already allowlists `coverartarchive.org`,
  `commons.wikimedia.org`, `upload.wikimedia.org`.

## What to do, in order

1. **Rebuild the backend image so `seed.band_art` is present**

   ```bash
   cd backend && docker compose build hc_archives_back && docker compose up -d hc_archives_back
   ```

   Verify: `docker compose exec hc_archives_back ls /app/seed/` shows
   `band_art.py`. Until rebuilt, `python -m seed.band_art` fails with
   `No module named seed.band_art`.

2. **Make sure the MB mirror is still running**

   ```bash
   cd ~/repos/musicbrainz-docker && docker compose ps
   ```

   Both `db` and `valkey` should be `Up`. If not, `docker compose up -d`. The
   pgdata volume persists, so no re-import is needed.

3. **Run `seed.cover_art` (the long one)**

   ```bash
   docker compose exec hc_archives_back python -m seed.cover_art
   ```

   - Serial HEAD requests to coverartarchive.org for each of ~13k albums with a
     `release_group_mbid`. Previous run was killed at ~66 min with no progress
     visible; expected total is probably 1–2 hours.
   - Script commits once at the end. Idempotent: only touches albums where
     `art IS NULL`.
   - **Open improvement (optional but worth it before re-running):** the
     script has no per-album logging and no incremental commit. Consider:
     - Logging every N (e.g. 200) albums with running totals.
     - Committing in chunks so a kill doesn't lose the whole pass.
     - Adding a small `time.sleep(0.1)` between requests to stay polite — CAA
       has no documented limit but this is a courteous default.

4. **Run `seed.band_art`**

   ```bash
   docker compose exec hc_archives_back python -m seed.band_art
   ```

   - Looks up each band's Wikidata QID via MB's `l_artist_url`, batches up to
     50 QIDs per Wikidata `wbgetentities` call, reads `P18` / `P154` claims,
     writes `Special:FilePath` URLs.
   - Should finish in a few minutes (~30 API calls for ~1.5k QIDs).
   - Idempotent: only fills `band_picture` / `logo` that are still null.

5. **Verify coverage**

   ```sql
   SELECT
     count(*) FILTER (WHERE art IS NOT NULL)  AS albums_with_art,
     count(*)                                 AS albums_total
   FROM album;

   SELECT
     count(*) FILTER (WHERE band_picture IS NOT NULL) AS bands_with_picture,
     count(*) FILTER (WHERE logo IS NOT NULL)         AS bands_with_logo,
     count(*)                                         AS bands_total
   FROM band;
   ```

   Spot-check a few: load `/band/{id}` and `/release/{id}` in the running app
   and confirm `BandCard` / `AlbumCard` render the images (next/image will
   refuse non-allowlisted hosts, which is the smoke test for
   `next.config.mjs`).

## Known issues to clean up alongside

- `tests/test_seed.py::test_seed_links_curated_subgenres` fails on `main`:
  asserts `emo` is dropped, but `emo` was added to `CURATED_GENRES`. Either
  the test or the curated vocabulary needs to be updated — separate from this
  work but lives in the same test file.
- `seed/cover_art.py` could grow the logging/chunked-commit improvements
  described in step 3. Worth doing before a full re-run.

## Out of scope (revisit later)

- A real CDN / cache layer for art. Today we link directly to coverartarchive
  redirects and `Special:FilePath` redirects to upload.wikimedia.org. Fine for
  now; revisit if image-load latency becomes a UX problem.
- Backfilling band art via fanart.tv or Discogs for bands with no Wikidata
  link. We tracked stats (`no_wikidata`) but didn't fall back.
- Refreshing existing art when MB or Wikidata adds new images. Both seeds are
  fill-only; they never overwrite.

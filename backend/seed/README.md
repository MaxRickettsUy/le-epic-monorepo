# Seed scripts

The catalogue is populated from a local MusicBrainz Postgres dump
(`metabrainz/musicbrainz-docker`). The scripts here are run by hand against
that DB; the running API never calls them.

| Module                | Purpose                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------ |
| `seed.mb_dump`        | Upsert bands/albums/members/genres by MBID. Idempotent. Scoped to `settings.seed_tag`.           |
| `seed.cover_art`      | Fill `album.art` from the Cover Art Archive.                                                     |
| `seed.band_art`       | Fill `band.band_picture` from MusicBrainz artist images.                                         |
| `seed.dev`            | Quick local fixture seed for development.                                                        |
| `seed.outliers`       | Audit the catalogue for likely off-genre bands. **Read-only — does not mutate the DB.**          |

Run from `backend/` with the venv active.

## `seed.outliers` — finding off-genre bands

Every band in the catalogue was seeded because MusicBrainz tagged it
"hardcore punk" (`settings.seed_tag`), but tag strength varies wildly. A band
with one "hardcore punk" vote and twenty "indie rock" votes is almost
certainly a false positive; a band with thirty "hardcore punk" votes and five
"metalcore" votes is the real deal.

This script joins the app DB against the MB dump and ranks each band by the
share of its total tag votes that the seed tag holds. Low share + loud
off-genre tags = likely outlier.

```bash
python -m seed.outliers              # print top 50 candidates as a table
python -m seed.outliers --limit 200  # widen the cut
python -m seed.outliers --csv > outliers.csv
```

The table columns are:

- `id` — app band id (use for `/band/{id}` lookups and `/band/{id}/update`).
- `share` — seed-tag votes ÷ total tag votes for that band on MB.
- `seed/total` — raw vote counts; helps distinguish a 1/2 band from a 30/60.
- `name`, `top other tags` — the top five non-seed tags with their MB vote
  counts, the easiest signal that something is off-genre.

Bands with no MB tags at all (`total = 0`) sink to the bottom — there's
nothing to say about them.

### Recommended workflow

1. Run the script and open the CSV.
2. For each candidate, decide:
   - **Doesn't belong** → `DELETE /band/{id}/delete` (cascades albums/members).
   - **Belongs but is a borderline / off-genre inclusion** → set a short
     `inclusion_reason` via the band edit form or `POST /band/{id}/update`,
     e.g. "Included for split LP with X". The note renders on the band
     detail page so the catalogue's reasoning is visible.
   - **Belongs, no note needed** → leave it.
3. Re-run the script after a fresh `seed.mb_dump` to recheck.

The script is read-only and idempotent; it never writes `inclusion_reason` or
deletes bands. Those decisions are intentionally manual.

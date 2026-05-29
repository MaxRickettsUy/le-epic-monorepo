# API Contract — le-epic frontend ⇄ backend

The Next.js app (`app/`) is a pure client of the FastAPI backend (`backend/`). It
owns no data; all reads and writes go over HTTP. This document is the contract
the frontend depends on. The authoritative definitions live in:

- **Backend:** `backend/app/schemas.py` (Pydantic) + the route modules under
  `backend/app/*/routes.py`.
- **Frontend:** `app/lib/schemas/index.ts` (zod). These mirror the Pydantic
  shapes and are validated against **every** response at the network boundary in
  `app/lib/api/client.ts`. A 2xx response that doesn't match throws
  `ApiParseError`, which surfaces through the nearest `error.tsx`.

## Connection

- Base URL: `process.env.API_URL` (server-only; defaults to
  `http://127.0.0.1:8000`). It is **not** exposed to the browser — all fetches
  run in Server Components / Server Actions.
- Content type: JSON. Request bodies set `Content-Type: application/json`.
- Backend rejects unknown fields on write bodies with a `422` (`extra="forbid"`).

## Conventions

- Columns are `snake_case` on the wire and in the TS types.
- `404` on a detail GET is mapped to `null` by `apiFetchOrNull`, letting pages
  render `not-found.tsx` instead of throwing.
- Reviews are out of MVP: `avg_review` is always `0`, `review_count` always `0`,
  and band `members` is always `[]`.

## Endpoints

### Bands

| Method & path                     | Request body | Response (2xx)                      | Notes                                                                                                                                                                                                             |
| --------------------------------- | ------------ | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /band/`                      | —            | `BandList`                          | `?page=` (1-based), `bands_per_page` from backend settings. `?sort=` is `name` (default) or `recent` (created_at desc). Optional facets, combinable: `?genre=<slug>`, `?country=<exact>`, `?letter=<A–Z or #>` (`#` = name not starting A–Z; other values → `422`). The pagination total reflects the active facets. |
| `GET /band/countries`             | —            | `CountryCount[]`                    | Distinct band countries with counts, desc by count then name. Free-text column (no normalization). Used to populate the country browse facet.                                                                     |
| `GET /band/{id}`                  | —            | `BandDetail`                        | `404` → `null`. Eager-loads `releases` + `members` + `genres`.                                                                                                                                                    |
| `GET /band/{id}/similar`          | —            | `SimilarBand[]`                     | Weighted score over shared members, `location`, shared genres, `label`, `country` (see `band/routes.py` `SIMILARITY_WEIGHTS`). Self excluded, score-desc then name, capped at `bands_per_page`. `404` if missing. |
| `POST /band/new`                  | `BandCreate` | `{ message: string, id: number }`   |                                                                                                                                                                                                                   |
| `POST /band/{id}/update`          | `BandCreate` | `"band updated"` (bare JSON string) | `404` if missing.                                                                                                                                                                                                 |
| `DELETE /band/{id}/delete`        | —            | `"band deleted"`                    | Not used by the frontend yet.                                                                                                                                                                                     |
| `GET /band/search?name=`          | —            | MusicBrainz passthrough             | `503` on upstream error. Not wired into UI yet.                                                                                                                                                                   |
| `GET /band/search_releases?mbid=` | —            | MusicBrainz passthrough             | `404` / `503`. Not wired into UI yet.                                                                                                                                                                             |

### Releases

| Method & path                 | Request body    | Response (2xx)                    | Notes                                                                    |
| ----------------------------- | --------------- | --------------------------------- | ------------------------------------------------------------------------ |
| `GET /release/{id}`           | —               | `ReleaseDetail`                   | `404` → `null`. Includes nested `band` summary + sorted `tracks`.        |
| `POST /release/new?band=`     | `ReleaseCreate` | `{ message: string, id: number }` | `band` query param is the parent band id; `404` if that band is missing. |
| `POST /release/{id}/update`   | `ReleaseCreate` | `"release update successful"`     | `404` if missing.                                                        |
| `DELETE /release/{id}/delete` | —               | `"release delete successful"`     | Not used by the frontend yet.                                            |

### Tracks

| Method & path               | Request body  | Response (2xx)    | Notes                                           |
| --------------------------- | ------------- | ----------------- | ----------------------------------------------- |
| `GET /track/{id}`           | —             | `TrackOut`        | Not wired into UI yet.                          |
| `POST /track/new?release=`  | `TrackCreate` | `{ message, id }` | `release` query param is the parent release id. |
| `POST /track/{id}/update`   | `TrackCreate` | `"track updated"` |                                                 |
| `DELETE /track/{id}/delete` | —             | `"track deleted"` |                                                 |

### Genres

| Method & path | Request body | Response (2xx) | Notes                                                                                                                                       |
| ------------- | ------------ | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /genre/` | —            | `Genre[]`      | The full curated sub-genre vocabulary, alphabetical by display name. Served from `backend/app/genres.py` (works even before the seed runs). |

### Search

| Method & path     | Request body | Response (2xx)  | Notes                                                                                                                                                                                                                                                                                                                                                                |
| ----------------- | ------------ | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /search/?q=` | —            | `SearchResults` | Case-insensitive substring match on **local** band name + `location` + genre name, and album name (LIKE wildcards in `q` are escaped). `q` required and non-blank after trimming (`422` otherwise). Optional `?genre=<slug>` restricts band results to that curated slug. Capped at 20 results per type. Distinct from the `/band/search*` MusicBrainz passthroughs. |

### Meta

| Method & path | Response           | Notes           |
| ------------- | ------------------ | --------------- |
| `GET /health` | `{ status: "ok" }` | Liveness check. |

## Payload shapes

Field optionality below uses `?` for "may be absent or null" — the zod schemas
use `.nullish()`, accepting `null` and `undefined`.

### `BandList` — `GET /band/`

```json
{
  bands: BandListItem[];
  next: number | null;   // next page number, or null at the end
  prev: number | null;   // previous page number, or null on page 1
}
```

### `CountryCount` — `GET /band/countries`

```json
{ country: string; count: number; }
```

### `BandListItem` / `BandBase`

```json
{
  id: number;
  name: string;
  status: "active" | "unknown" | "on-hold" | "split-up";
  band_picture?: string;
  logo?: string;
  location: string;
  country: string;
  label: string;
  mbid?: string;
  begin_year?: number;  // year formed (from MB artist.begin_date_year); year-only
  end_year?: number;    // year disbanded (from MB artist.end_date_year); null if active/unknown
  genres: Genre[];       // curated sub-genres, strongest-voted first; [] if none
}
```

### `Genre`

A curated hardcore sub-genre. `slug` is the stable id (e.g. `nyhc`), `name` the
display label (e.g. `NYHC`).

```json
{ slug: string; name: string; }
```

### `BandDetail` — `GET /band/{id}` (extends `BandBase`)

```json
{
  ...BandBase,
  members: Member[];     // always [] in MVP
  releases: Release[];   // releases nested under the band (no band back-ref)
}
```

### `Member`

```json
{ name: string; role?: string; }
```

### `SimilarBand` — `GET /band/{id}/similar`

`score` is the weighted sum; the remaining fields expose which factors
contributed (so the UI can render "why").

```json
{
  id: number;
  name: string;
  location: string;
  country: string;
  score: number;
  shared_members: number;
  shared_genres: number;
  same_location: boolean;
  same_label: boolean;
  same_country: boolean;
}
```

### `Release` (nested under a band)

```json
{
  id: number;
  band_id: number;
  name: string;
  length?: number;
  art?: string;
  release_type?: string;
  type?: string;              // computed alias of release_type
  label?: string;
  year?: number;
  release_group_mbid?: string;
  avg_review: number;         // always 0 in MVP
  review_count: number;       // always 0 in MVP
}
```

### `ReleaseDetail` — `GET /release/{id}` (extends `Release`)

```json
{
  ...Release,
  band: BandSummary;
  tracks: Track[];            // sorted by position (nulls last)
}
```

### `BandSummary` (nested under a release detail)

```json
{ id: number; name: string; location: string; country: string; label: string; }
```

### `Track` / `TrackOut`

```json
{
  id: number;
  name: string;
  length?: number;
  lyrics?: string;
  track_number?: number;
  position?: number;
  mbid?: string;
}
```

### `SearchResults` — `GET /search/?q=`

```json
{
  query: string;              // the (trimmed) query that was run
  bands: BandSearchItem[];
  albums: AlbumSearchItem[];
}
```

### `BandSearchItem`

```json
{
  id: number;
  name: string;
  location: string;
  country: string;
  genres: Genre[];        // curated sub-genres, strongest-voted first; [] if none
}
```

### `AlbumSearchItem`

`band_id` / `band_name` are the owning band, so a result row can link to either
the album (`/release/{id}`) or its band.

```json
{
  id: number;
  name: string;
  year?: number;
  art?: string;
  band_id: number;
  band_name: string;
}
```

## Request bodies

### `BandCreate` — `POST /band/new`, `POST /band/{id}/update`

```json
{
  name: string;
  status: string;
  band_picture?: string;
  logo?: string;
  location: string;
  country: string;
  label: string;
}
```

### `ReleaseCreate` — `POST /release/new`, `POST /release/{id}/update`

```json
{
  name: string;
  length?: number;
  art?: string;
  release_type?: string;
  label?: string;
  year?: number;
}
```

### `TrackCreate` — `POST /track/new`, `POST /track/{id}/update`

```json
{
  name: string;
  track_number: number;
  length?: number;
  lyrics?: string;
}
```

## Keeping the contract in sync

When `backend/app/schemas.py` changes, update `app/lib/schemas/index.ts` to
match and this document alongside. Because responses are validated at the
boundary, an undocumented drift fails loudly (`ApiParseError`) rather than
silently rendering wrong data.

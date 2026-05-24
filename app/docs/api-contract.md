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

| Method & path                     | Request body | Response (2xx)                      | Notes                                                       |
| --------------------------------- | ------------ | ----------------------------------- | ----------------------------------------------------------- |
| `GET /band/`                      | —            | `BandList`                          | `?page=` (1-based), `bands_per_page` from backend settings. |
| `GET /band/{id}`                  | —            | `BandDetail`                        | `404` → `null`. Eager-loads `releases` + `members`.         |
| `POST /band/new`                  | `BandCreate` | `{ message: string, id: number }`   |                                                             |
| `POST /band/{id}/update`          | `BandCreate` | `"band updated"` (bare JSON string) | `404` if missing.                                           |
| `DELETE /band/{id}/delete`        | —            | `"band deleted"`                    | Not used by the frontend yet.                               |
| `GET /band/search?name=`          | —            | MusicBrainz passthrough             | `503` on upstream error. Not wired into UI yet.             |
| `GET /band/search_releases?mbid=` | —            | MusicBrainz passthrough             | `404` / `503`. Not wired into UI yet.                       |

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

### `BandListItem` / `BandBase`

```json
{
  id: number;
  name: string;
  status: "active" | "unknown" | "on-hold" | "split-up";
  band_picture?: string;
  location: string;
  country: string;
  label: string;
  mbid?: string;
}
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

## Request bodies

### `BandCreate` — `POST /band/new`, `POST /band/{id}/update`

```json
{
  name: string;
  status: string;
  band_picture?: string;
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

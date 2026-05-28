// Zod schemas for the backend response contract. These are the single source
// of truth for API payload shapes — `lib/types.ts` re-exports the inferred
// types, and `lib/api/*` validates every response against them at the network
// boundary (see ./client.ts). Shapes mirror ../../backend/app/schemas.py.

import { z } from "zod";

export const bandStatusSchema = z.enum(["active", "unknown", "on-hold", "split-up"]);

export const memberSchema = z.object({
  name: z.string(),
  role: z.string().nullish(),
});

/** A curated hardcore sub-genre attached to a band. */
export const genreSchema = z.object({
  slug: z.string(),
  name: z.string(),
});

export const trackSchema = z.object({
  id: z.number(),
  name: z.string(),
  length: z.number().nullish(),
  lyrics: z.string().nullish(),
  track_number: z.number().nullish(),
  position: z.number().nullish(),
  mbid: z.string().nullish(),
});

/** Release as nested under a band (no back-reference to the band). */
export const releaseSchema = z.object({
  id: z.number(),
  band_id: z.number(),
  name: z.string(),
  length: z.number().nullish(),
  art: z.string().nullish(),
  release_type: z.string().nullish(),
  /** Alias of `release_type` provided by the backend (computed field). */
  type: z.string().nullish(),
  label: z.string().nullish(),
  year: z.number().nullish(),
  release_group_mbid: z.string().nullish(),
  avg_review: z.number(),
  review_count: z.number(),
});

/** Band as nested under a release detail response. */
export const bandSummarySchema = z.object({
  id: z.number(),
  name: z.string(),
  location: z.string(),
  country: z.string(),
  label: z.string(),
});

/** Release detail response (`GET /release/{id}`). */
export const releaseDetailSchema = releaseSchema.extend({
  band: bandSummarySchema,
  tracks: z.array(trackSchema),
});

const bandBaseSchema = z.object({
  id: z.number(),
  name: z.string(),
  status: bandStatusSchema,
  band_picture: z.string().nullish(),
  logo: z.string().nullish(),
  location: z.string(),
  country: z.string(),
  label: z.string(),
  mbid: z.string().nullish(),
  begin_year: z.number().nullish(),
  end_year: z.number().nullish(),
  /** Curated sub-genres, strongest-voted first. */
  genres: z.array(genreSchema),
});

/** Band as returned in the paginated list (`GET /band/`). */
export const bandListItemSchema = bandBaseSchema;

/** Band detail response (`GET /band/{id}`). */
export const bandSchema = bandBaseSchema.extend({
  members: z.array(memberSchema),
  releases: z.array(releaseSchema),
});

/**
 * A band scored as similar (`GET /band/{id}/similar`). `score` is a weighted
 * sum; the remaining fields expose which factors contributed, for the UI.
 */
export const similarBandSchema = z.object({
  id: z.number(),
  name: z.string(),
  location: z.string(),
  country: z.string(),
  score: z.number(),
  shared_members: z.number(),
  shared_genres: z.number(),
  same_location: z.boolean(),
  same_label: z.boolean(),
  same_country: z.boolean(),
});

/** Paginated band list envelope (`GET /band/`). */
export const bandListSchema = z.object({
  bands: z.array(bandListItemSchema),
  next: z.number().nullable(),
  prev: z.number().nullable(),
});

/** A band matched by a catalogue search (`GET /search/`). */
export const bandSearchItemSchema = z.object({
  id: z.number(),
  name: z.string(),
  location: z.string(),
  country: z.string(),
  /** Curated sub-genres, strongest-voted first. */
  genres: z.array(genreSchema),
});

/** An album matched by a catalogue search, carrying its band for linking. */
export const albumSearchItemSchema = z.object({
  id: z.number(),
  name: z.string(),
  year: z.number().nullish(),
  art: z.string().nullish(),
  band_id: z.number(),
  band_name: z.string(),
});

/** Combined search results across bands and albums (`GET /search/?q=`). */
export const searchResultsSchema = z.object({
  query: z.string(),
  bands: z.array(bandSearchItemSchema),
  albums: z.array(albumSearchItemSchema),
});

/** Write response from `POST /band/new` and `POST /release/new`. */
export const mutationResultSchema = z.object({
  message: z.string(),
  id: z.number(),
});

// ── Form input schemas ──────────────────────────────────────────────
// These validate user input in the create/edit forms (react-hook-form +
// zodResolver). They are deliberately separate from the response schemas
// above: no server-assigned fields (id, avg_review, …) and stricter
// required-field rules than the permissive API contract. The inferred
// types are structurally compatible with `BandCreateInput` /
// `ReleaseCreateInput` in `lib/api/`, so resolved values submit directly.

export const bandFormSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  status: bandStatusSchema,
  country: z.string().trim().min(1, "Country is required"),
  location: z.string().trim(),
  label: z.string().trim(),
  band_picture: z.string().nullish(),
  logo: z.string().nullish(),
});

export const releaseFormSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  year: z.coerce.number().int().min(1900).max(2100).nullish(),
  release_type: z.string().nullish(),
  label: z.string().nullish(),
  length: z.number().nullish(),
  art: z.string().nullish(),
});

export type BandFormValues = z.infer<typeof bandFormSchema>;
export type ReleaseFormValues = z.infer<typeof releaseFormSchema>;

export type BandStatus = z.infer<typeof bandStatusSchema>;
export type Member = z.infer<typeof memberSchema>;
export type Genre = z.infer<typeof genreSchema>;
export type Track = z.infer<typeof trackSchema>;
export type Release = z.infer<typeof releaseSchema>;
export type BandSummary = z.infer<typeof bandSummarySchema>;
export type SimilarBand = z.infer<typeof similarBandSchema>;
export type ReleaseDetail = z.infer<typeof releaseDetailSchema>;
export type BandListItem = z.infer<typeof bandListItemSchema>;
export type Band = z.infer<typeof bandSchema>;
export type BandList = z.infer<typeof bandListSchema>;
export type MutationResult = z.infer<typeof mutationResultSchema>;
export type BandSearchItem = z.infer<typeof bandSearchItemSchema>;
export type AlbumSearchItem = z.infer<typeof albumSearchItemSchema>;
export type SearchResults = z.infer<typeof searchResultsSchema>;

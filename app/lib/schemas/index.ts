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
  location: z.string(),
  country: z.string(),
  label: z.string(),
  mbid: z.string().nullish(),
});

/** Band as returned in the paginated list (`GET /band/`). */
export const bandListItemSchema = bandBaseSchema;

/** Band detail response (`GET /band/{id}`). */
export const bandSchema = bandBaseSchema.extend({
  members: z.array(memberSchema),
  releases: z.array(releaseSchema),
});

/** Paginated band list envelope (`GET /band/`). */
export const bandListSchema = z.object({
  bands: z.array(bandListItemSchema),
  next: z.number().nullable(),
  prev: z.number().nullable(),
});

/** Write response from `POST /band/new` and `POST /release/new`. */
export const mutationResultSchema = z.object({
  message: z.string(),
  id: z.number(),
});

export type BandStatus = z.infer<typeof bandStatusSchema>;
export type Member = z.infer<typeof memberSchema>;
export type Track = z.infer<typeof trackSchema>;
export type Release = z.infer<typeof releaseSchema>;
export type BandSummary = z.infer<typeof bandSummarySchema>;
export type ReleaseDetail = z.infer<typeof releaseDetailSchema>;
export type BandListItem = z.infer<typeof bandListItemSchema>;
export type Band = z.infer<typeof bandSchema>;
export type BandList = z.infer<typeof bandListSchema>;
export type MutationResult = z.infer<typeof mutationResultSchema>;

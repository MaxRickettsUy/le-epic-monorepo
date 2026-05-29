import { z } from "zod";
import type {
  Band,
  BandList,
  BandStatus,
  CountryCount,
  Genre,
  MutationResult,
  SimilarBand,
} from "@/lib/types";
import {
  bandListSchema,
  bandSchema,
  countryCountSchema,
  genreSchema,
  mutationResultSchema,
  similarBandSchema,
} from "@/lib/schemas";
import { apiFetch, apiFetchOrNull } from "./client";

export interface BandCreateInput {
  name: string;
  status: BandStatus;
  location: string;
  country: string;
  label: string;
  band_picture?: string | null;
  logo?: string | null;
}

export type { MutationResult };

/** Browse facets for the band index. All optional and combinable. */
export interface BandListFilters {
  page?: number;
  sort?: "name" | "recent";
  /** Curated genre slug. */
  genre?: string;
  /** Exact country string (as returned by `listCountries`). */
  country?: string;
  /** Single A–Z initial, or `#` for names not starting with a letter. */
  letter?: string;
}

/** Paginated, optionally-faceted list of bands (`GET /band/`). */
export function listBands(filters: BandListFilters = {}): Promise<BandList> {
  const params = new URLSearchParams();
  params.set("page", String(filters.page ?? 1));
  params.set("sort", filters.sort ?? "name");
  if (filters.genre) params.set("genre", filters.genre);
  if (filters.country) params.set("country", filters.country);
  if (filters.letter) params.set("letter", filters.letter);
  return apiFetch(`/band/?${params.toString()}`, bandListSchema, {
    next: { revalidate: 60 },
  });
}

/** The curated sub-genre vocabulary (`GET /genre/`), alphabetical by name. */
export function listGenres(): Promise<Genre[]> {
  return apiFetch(`/genre/`, z.array(genreSchema), { next: { revalidate: 3600 } });
}

/** Distinct band countries with counts (`GET /band/countries`). */
export function listCountries(): Promise<CountryCount[]> {
  return apiFetch(`/band/countries`, z.array(countryCountSchema), { next: { revalidate: 60 } });
}

/** Band detail (`GET /band/{id}`); `null` when the band does not exist. */
export function getBand(id: number): Promise<Band | null> {
  return apiFetchOrNull(`/band/${id}`, bandSchema, { next: { revalidate: 60 } });
}

/**
 * Bands ranked by a weighted similarity score (`GET /band/{id}/similar`),
 * combining shared members, location, label, and country. Returns `[]` when the
 * band has no similar bands or does not exist.
 */
export async function getSimilarBands(id: number): Promise<SimilarBand[]> {
  const result = await apiFetchOrNull(`/band/${id}/similar`, z.array(similarBandSchema), {
    next: { revalidate: 60 },
  });
  return result ?? [];
}

export function createBand(input: BandCreateInput): Promise<MutationResult> {
  return apiFetch(`/band/new`, mutationResultSchema, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateBand(id: number, input: BandCreateInput): Promise<string> {
  return apiFetch(`/band/${id}/update`, z.string(), {
    method: "POST",
    body: JSON.stringify(input),
  });
}

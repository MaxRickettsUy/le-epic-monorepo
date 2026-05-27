import { z } from "zod";
import type { Band, BandList, BandStatus, MutationResult, SimilarBand } from "@/lib/types";
import { bandListSchema, bandSchema, mutationResultSchema, similarBandSchema } from "@/lib/schemas";
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

/** Paginated list of bands (`GET /band/`). `sort` is `name` (default) or `recent`. */
export function listBands(page = 1, sort: "name" | "recent" = "name"): Promise<BandList> {
  return apiFetch(`/band/?page=${page}&sort=${sort}`, bandListSchema, {
    next: { revalidate: 60 },
  });
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

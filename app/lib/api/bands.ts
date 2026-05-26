import { z } from "zod";
import type { Band, BandList, BandStatus, MutationResult, SimilarBand } from "@/lib/types";
import {
  bandListSchema,
  bandSchema,
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

/** Bands from the same scene (`GET /band/{id}/similar`); `[]` when the band has none. */
export function getSimilarBands(id: number): Promise<SimilarBand[]> {
  return apiFetch(`/band/${id}/similar`, z.array(similarBandSchema), {
    next: { revalidate: 60 },
  });
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

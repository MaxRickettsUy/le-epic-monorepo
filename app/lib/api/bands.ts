import type { Band, BandList, BandStatus } from "@/lib/types";
import { apiFetch, apiFetchOrNull } from "./client";

export interface BandCreateInput {
  name: string;
  status: BandStatus;
  location: string;
  country: string;
  label: string;
  band_picture?: string | null;
}

export interface MutationResult {
  message: string;
  id: number;
}

/** Paginated list of bands (`GET /band/`). */
export function listBands(page = 1): Promise<BandList> {
  return apiFetch<BandList>(`/band/?page=${page}`, { next: { revalidate: 60 } });
}

/** Band detail (`GET /band/{id}`); `null` when the band does not exist. */
export function getBand(id: number): Promise<Band | null> {
  return apiFetchOrNull<Band>(`/band/${id}`, { next: { revalidate: 60 } });
}

export function createBand(input: BandCreateInput): Promise<MutationResult> {
  return apiFetch<MutationResult>(`/band/new`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateBand(id: number, input: BandCreateInput): Promise<string> {
  return apiFetch<string>(`/band/${id}/update`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

import { z } from "zod";
import type { MutationResult, ReleaseDetail, ReleaseList } from "@/lib/types";
import { mutationResultSchema, releaseDetailSchema, releaseListSchema } from "@/lib/schemas";
import { apiFetch, apiFetchOrNull } from "./client";

export interface ReleaseCreateInput {
  name: string;
  length?: number | null;
  art?: string | null;
  release_type?: string | null;
  label?: string | null;
  year?: number | null;
}

export interface ReleaseListFilters {
  page?: number;
  sort?: "recent" | "year";
}

/** Paginated list of releases for catalogue discovery (`GET /release/`). */
export function listReleases(filters: ReleaseListFilters = {}): Promise<ReleaseList> {
  const params = new URLSearchParams();
  params.set("page", String(filters.page ?? 1));
  params.set("sort", filters.sort ?? "recent");
  return apiFetch(`/release/?${params.toString()}`, releaseListSchema, {
    next: { revalidate: 60 },
  });
}

/** Release detail (`GET /release/{id}`); `null` when the release does not exist. */
export function getRelease(id: number): Promise<ReleaseDetail | null> {
  return apiFetchOrNull(`/release/${id}`, releaseDetailSchema, { next: { revalidate: 60 } });
}

export function createRelease(bandId: number, input: ReleaseCreateInput): Promise<MutationResult> {
  return apiFetch(`/release/new?band=${bandId}`, mutationResultSchema, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateRelease(id: number, input: ReleaseCreateInput): Promise<string> {
  return apiFetch(`/release/${id}/update`, z.string(), {
    method: "POST",
    body: JSON.stringify(input),
  });
}

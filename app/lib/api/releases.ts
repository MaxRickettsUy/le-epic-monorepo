import { z } from "zod";
import type { MutationResult, ReleaseDetail } from "@/lib/types";
import { mutationResultSchema, releaseDetailSchema } from "@/lib/schemas";
import { apiFetch, apiFetchOrNull } from "./client";

export interface ReleaseCreateInput {
  name: string;
  length?: number | null;
  art?: string | null;
  release_type?: string | null;
  label?: string | null;
  year?: number | null;
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

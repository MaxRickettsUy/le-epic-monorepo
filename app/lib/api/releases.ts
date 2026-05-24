import type { ReleaseDetail } from "@/lib/types";
import { apiFetch, apiFetchOrNull } from "./client";
import type { MutationResult } from "./bands";

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
  return apiFetchOrNull<ReleaseDetail>(`/release/${id}`, { next: { revalidate: 60 } });
}

export function createRelease(bandId: number, input: ReleaseCreateInput): Promise<MutationResult> {
  return apiFetch<MutationResult>(`/release/new?band=${bandId}`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateRelease(id: number, input: ReleaseCreateInput): Promise<string> {
  return apiFetch<string>(`/release/${id}/update`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

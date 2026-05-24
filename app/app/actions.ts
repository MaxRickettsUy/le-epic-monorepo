"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import {
  createBand,
  updateBand,
  createRelease,
  updateRelease,
  type BandCreateInput,
  type ReleaseCreateInput,
} from "@/lib/api";

export async function createBandAction(input: BandCreateInput) {
  const { id } = await createBand(input);
  revalidatePath("/");
  redirect(`/band/${id}`);
}

export async function updateBandAction(id: number, input: BandCreateInput) {
  await updateBand(id, input);
  revalidatePath("/");
  revalidatePath(`/band/${id}`);
  redirect(`/band/${id}`);
}

export async function createReleaseAction(bandId: number, input: ReleaseCreateInput) {
  const { id } = await createRelease(bandId, input);
  revalidatePath(`/band/${bandId}`);
  redirect(`/release/${id}`);
}

export async function updateReleaseAction(id: number, bandId: number, input: ReleaseCreateInput) {
  await updateRelease(id, input);
  revalidatePath(`/band/${bandId}`);
  revalidatePath(`/release/${id}`);
  redirect(`/release/${id}`);
}

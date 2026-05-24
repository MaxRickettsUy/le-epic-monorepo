import { notFound } from "next/navigation";
import { getRelease } from "@/lib/api";
import { EditReleaseForm } from "./edit-release-form";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const releaseId = Number(id);
  if (!Number.isInteger(releaseId) || releaseId <= 0) notFound();

  const release = await getRelease(releaseId);

  if (!release) notFound();

  return <EditReleaseForm release={release} />;
}

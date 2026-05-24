import { notFound } from "next/navigation";
import { getBand } from "@/lib/api";
import { EditBandForm } from "./edit-band-form";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const bandId = Number(id);
  if (!Number.isInteger(bandId) || bandId <= 0) notFound();

  const band = await getBand(bandId);

  if (!band) notFound();

  return <EditBandForm band={band} />;
}

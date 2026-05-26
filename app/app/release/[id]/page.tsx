import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getRelease } from "@/lib/api";
import { TracksTable } from "./table";
import { AlbumBreadcrumbs } from "./breadcrumbs";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Header } from "@/components/ui/header";
import { TopSection } from "@/components/TopSection";

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  const releaseId = Number(id);
  if (!Number.isInteger(releaseId) || releaseId <= 0) return { title: "Release not found" };
  const release = await getRelease(releaseId);
  return { title: release ? `${release.band.name} – ${release.name}` : "Release not found" };
}

export default async function ReleasePage({ params }: PageProps) {
  const { id } = await params;
  const releaseId = Number(id);
  if (!Number.isInteger(releaseId) || releaseId <= 0) notFound();

  const release = await getRelease(releaseId);

  if (!release) notFound();

  return (
    <main className="flex-col pb-[1rem]">
      <Header />
      <div className="flex flex-col gap-[1rem] p-[1rem]">
        <AlbumBreadcrumbs band={release.band.name} name={release.name} id={release.band_id} />
        <div className="flex flex-col gap-[1rem] p-4 md:flex-row">
          <TopSection id={release.band_id} name={release.band.name} picture={release.art} />
          <Tabs defaultValue="tracks" className="w-full p-4">
            <TabsList>
              <TabsTrigger value="tracks">Tracks</TabsTrigger>
            </TabsList>
            <TabsContent className="w-full" value="tracks">
              <TracksTable tracks={release.tracks} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </main>
  );
}

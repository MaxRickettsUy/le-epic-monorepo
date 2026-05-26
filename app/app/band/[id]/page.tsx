import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getBand } from "@/lib/api";
import { DiscographyTable } from "./discog";
import { MemberTable } from "./members";
import { Header } from "@/components/ui/header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TopSection } from "@/components/TopSection";

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  const bandId = Number(id);
  if (!Number.isInteger(bandId) || bandId <= 0) return { title: "Band not found" };
  const band = await getBand(bandId);
  return { title: band ? band.name : "Band not found" };
}

export default async function BandPage({ params }: PageProps) {
  const { id } = await params;
  const bandId = Number(id);
  if (!Number.isInteger(bandId) || bandId <= 0) notFound();

  const band = await getBand(bandId);

  if (!band) notFound();

  const releases = [...band.releases].sort((a, b) => (a.year ?? 0) - (b.year ?? 0));

  return (
    <main className="flex-col pb-[1rem]">
      <Header />
      <div className="flex flex-col gap-[1rem] p-4 md:flex-row">
        <TopSection id={band.id} name={band.name} picture={band.band_picture} />
        <Tabs defaultValue="discography" className="w-full p-4">
          <TabsList>
            <TabsTrigger value="discography">Discography</TabsTrigger>
            <TabsTrigger value="members">Members</TabsTrigger>
          </TabsList>
          <TabsContent className="w-full" value="discography">
            <DiscographyTable releases={releases} />
          </TabsContent>
          <TabsContent value="members">
            <MemberTable members={band.members} />
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}

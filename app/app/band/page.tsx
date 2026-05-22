'use client'

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Band } from "@/lib/types";
import { DiscographyTable } from "./discog";
import { MemberTable } from "./members";
import { Header } from "@/components/ui/header";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TopSection } from "@/components/TopSection";

const BandPage = () => {
  const searchParams = useSearchParams();
  const bandId = Number(searchParams.get("id"));
  const [band, setBand] = useState<Band | null>(null);

  useEffect(() => {
    if (!bandId) return;

    const fetchData = async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URI}:${process.env.NEXT_PUBLIC_API_PORT}/band/${bandId}`);
      const data = await res.json();
      const band: Band = { ...data, members: [] };
      setBand(band);
    };

    fetchData();
  }, [bandId]);

  console.log(band)

  return (
    <main className="py-[1rem] flex-col border border-red-500">
      <Header />
      <div className="py-[1rem] w-full">
        <Separator />
      </div>
      {band && (
        <div className="flex flex-col md:flex-row gap-[1rem] p-4 border border-red-500">
          <TopSection id={band.id} name={band.name} />
          <Tabs defaultValue="discography" className="w-full border border-red-500 p-4">
            <TabsList>
              <TabsTrigger value="discography">Discography</TabsTrigger>
              <TabsTrigger value="members">Members</TabsTrigger>
              <TabsTrigger value="similar-artists">Similar Artists</TabsTrigger>
              <TabsTrigger value="links">Links</TabsTrigger>
            </TabsList>
            <TabsContent className="w-full" value="discography">
              <DiscographyTable
                band={band.name}
                releases={band.releases.sort((a,b) => a.year - b.year) ?? []}
              />
            </TabsContent>
            <TabsContent value="members">
              <MemberTable band={band.name} members={band.members} />
            </TabsContent>
          </Tabs>
        </div>
      )}
    </main>
  );
};

export default BandPage;

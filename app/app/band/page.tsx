'use client'

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { createContext, useContext, useEffect, useState } from "react";
import { Band, Release } from "@/lib/types";
import { Discography } from "./discog";
import { faker } from "@faker-js/faker";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MemberTable } from "./members";
import { statusMap } from "@/lib/const";
import { Pencil } from "lucide-react"
import { Header } from "@/components/ui/header";

interface BandContextType {
  band: Band | null;
  setBand: (band: Band) => void;
}

interface ReleaseContextType {
  releases: Release[] | null;
  setReleases: (releases: Release[]) => void;
}

const BandContext = createContext<BandContextType>({
  band: null,
  setBand: () => {}
});

const BandPage = () => {
  const { band, setBand } = useContext(BandContext);
  const searchParams = useSearchParams();

  useEffect(() => {
    const id: number = Number(searchParams.get("id"));

    const fetchData = async (params: { id: number }) => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URI}:${process.env.NEXT_PUBLIC_API_PORT}/band/${params.id}`)

      return res.json();
    }

    if (id !== null) {
      fetchData({ id }).then((res: Band) => {
        const band: Band = {
          ...res,
          members: [],
        }

        setBand(band);
      })
    }
  }, [searchParams])

  return (
    <main className="py-[1rem] flex-col">
      <Header />
      <div className="py-[1rem] w-full">
        <Separator />
      </div>
      { band && (
          <div className="flex flex-col gap-[1rem] p-[1rem]">
            <div className="flex flex-row">
              <div className="flex flex-col gap-[1rem]">
                <div className="flex flex-row gap-[8]">
                  <span className="text-4xl">{band.name}</span>
                  <Link href={{ pathname: "/edit/band", query: { id: band.id }}}>
                    <Button variant="ghost" size="icon">
                      <Pencil />
                    </Button>
                  </Link>
                </div>
                <span>Status: {statusMap[band.status]}</span>
              </div>
              { band.name && (
                <img
                  className="ml-auto"
                  alt={band.name}
                  src={faker.image.urlLoremFlickr({ category: 'people' })}
                  width={250}
                  height={250}
                />
              )}
            </div>
            <Tabs defaultValue="discography">
              <TabsList>
                <TabsTrigger value="discography">Discography</TabsTrigger>
                <TabsTrigger value="members">Members</TabsTrigger>
                <TabsTrigger value="similar-artists">Similar Artists</TabsTrigger>
                <TabsTrigger value="links">Links</TabsTrigger>
              </TabsList>
              <TabsContent className="w-full" value="discography">
                <Discography band={band.name} releases={band.releases} />
              </TabsContent>
              <TabsContent value="members">
                <MemberTable band={band.name} members={band.members} />
              </TabsContent>
              {/* <TabsContent value="similar-artists">
                <SimilarArtistsTable band={band.name} albums={band.discography} />
              </TabsContent>
              <TabsContent value="links">
                { band.name && <LinksTable band={band.name} albums={band.discography} /> }
              </TabsContent> */}
            </Tabs>
            <Link
              href={{
                pathname: "/create/release",
                query: { band_id: band.id }
              }}
            >
              <Button className="w-[25%]">
                Add Release
              </Button>
            </Link>
          </div>
        )
      }
    </main>
  );
}

export default function Page() {
  const [band, setBand] = useState<Band | null>(null);

  return (
    <BandContext.Provider value={{ band, setBand }}>
      <BandPage />
    </BandContext.Provider>
  )
}

'use client'

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { createContext, useContext, useEffect, useState } from "react";
import { Band, Release } from "@/lib/types";
import { DiscographyTable } from "./discog";
import { faker } from "@faker-js/faker";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MemberTable } from "./members";
import { statusMap } from "@/lib/const";
import { Pencil } from "lucide-react"
import { Header } from "@/components/ui/header";
import { Badge } from "@/components/ui/badge";
import { Details } from "./details";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import Image from "next/image";

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

const TopSection = (props: {
  band: Band
}) => {
  console.log(props.band.id)

  return (
    <div className="flex flex-col md:flex-row lg:flex-row xl:flex-row items-center lg:items-start md:items-start xs:items-start gap-[1rem] lg:justify-between">
      <div className="flex flex-col gap-[1rem]">
        {/* <div className="flex flex-row gap-[8]">
          <span className="text-4xl">{props.band.name}</span>
          <Link href={{ pathname: "/edit/band", query: { id: props.band.id }}}>
            <Button variant="ghost" size="icon">
              <Pencil />
            </Button>
          </Link>
          <Badge>
            {statusMap[props.band.status]}
          </Badge>
        </div> */}
        <Card>
          <CardHeader>
            <CardTitle>{props.band.name}</CardTitle>
            <CardDescription>Insert City Hardcore</CardDescription>
          </CardHeader>
          <CardContent>
          { props.band.name && (
            <div className="relative">
              <Image
                className="lg:ml-auto xl:ml-auto rounded-sm"
                alt={props.band.name}
                src={faker.image.urlLoremFlickr({ category: 'people' })}
                width={250}
                height={250}
              />
              {/* <Badge
                className="w-max absolute top-[-10px] right-[-20px]"
              >
                {statusMap[props.band.status]}
              </Badge> */}
            </div>
          )}
          </CardContent>
          <CardFooter>
            <div className="flex flex-col gap-1 w-full">
              <Link
                href={{
                  pathname: "/edit/band",
                  query: { id: props.band.id }
                }}
              >
                <Button className="w-full">
                  Edit Band
                </Button>
              </Link>
              <Link
                href={{
                  pathname: "/create/release",
                  query: { band_id: props.band.id }
                }}
              >
                <Button className="w-full">
                  Add Release
                </Button>
              </Link>
            </div>
          </CardFooter>
        </Card>
      </div>
      {/* <Details {...props} /> */}
    </div>
  )

}
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
      fetchData({ id }).then((res) => {
        console.log(res)

        const band: Band = {
          ...res.band,
          members: [],
        }

        setBand(band);
      })
    }
  }, [searchParams])

  console.log(band)

  return (
    <main className="py-[1rem] flex-col">
      <Header />
      <div className="py-[1rem] w-full">
        <Separator />
      </div>
      { band && (
        <div className="flex flex-col md:flex-row lg:flex-row xl:flex-row gap-[1rem] p-[4]">
          <TopSection band={band} />
          <Tabs defaultValue="discography" className="w-full">
            <TabsList>
              <TabsTrigger value="discography">Discography</TabsTrigger>
              <TabsTrigger value="members">Members</TabsTrigger>
              <TabsTrigger value="similar-artists">Similar Artists</TabsTrigger>
              <TabsTrigger value="links">Links</TabsTrigger>
            </TabsList>
            <TabsContent className="w-full" value="discography">
              <DiscographyTable band={band.name} releases={band.releases ?? []} />
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
        </div>
      )}
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

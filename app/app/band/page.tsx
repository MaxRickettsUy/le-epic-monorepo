'use client'

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { createContext, useContext, useEffect, useState } from "react";
import { Band } from "@/lib/types";
import { DiscogTable } from "./discog";
import { faker } from "@faker-js/faker";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MemberTable } from "./members";
import { SimilarArtistsTable } from "./similar-artists";
import { LinksTable } from "./links";

const SearchInput = () => (
  <Input type="search" placeholder="Search..." />
);

interface BandContextType {
  band: Band | null;
  setBand: (band: Band) => void;
}

const BandContext = createContext<BandContextType>({
  band: null,
  setBand: () => {}
});

const Band = () => {
  const { band, setBand } = useContext(BandContext);
  const searchParams = useSearchParams();

  useEffect(() => {
    const name = searchParams.get("name");

    const fetchData = async (name: string) => {
      const res = await fetch('/api/band', {
        method: "POST",
        body: JSON.stringify({ name })
      });

      return res.json();
    }

    if (name !== null) {
      fetchData(name).then((res) =>{
        setBand(res);
      })
    }
  }, [searchParams])

  return (
    <main className="py-[1rem] flex-col">
      <div className="flex flex-row gap-[1rem] px-[1rem]">
        <Link href="/">
          <Avatar>
            <AvatarFallback>L</AvatarFallback>
          </Avatar>
        </Link>
        {/* <NavigationMenuDemo /> */}
        <div className="ml-auto flex flex-row gap-[1rem]">
          <Button>Add Band</Button>
          <SearchInput />
        </div>
        <Avatar>
          <AvatarFallback>U</AvatarFallback>
        </Avatar>
      </div>
      <div className="py-[1rem] w-full">
        <Separator />
      </div>
      {
        band && (
          <div className="flex flex-col gap-[1rem] p-[1rem]">
            <div className="flex flex-row">
              <div className="flex flex-col gap-[1rem]">
                <span className="text-4xl">{band.name}</span>
                <span>Status: active</span>
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
                <DiscogTable band={band.name} albums={band.discography} />
              </TabsContent>
              <TabsContent value="members">
                <MemberTable band={band.name} members={band.members} />
              </TabsContent>
              <TabsContent value="similar-artists">
                <SimilarArtistsTable band={band.name} albums={band.discography} />
              </TabsContent>
              <TabsContent value="links">
                { band.name && <LinksTable band={band.name} albums={band.discography} /> }
              </TabsContent>
            </Tabs>
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
      <Band />
    </BandContext.Provider>
  )
}

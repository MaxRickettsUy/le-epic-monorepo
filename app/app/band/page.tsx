'use client'

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Band } from "@/lib/types";
import { DiscographyTable } from "./discog";
import { MemberTable } from "./members";
import { statusMap } from "@/lib/const";
import { Header } from "@/components/ui/header";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import Image from "next/image";
import { faker } from "@faker-js/faker";
import { Pencil } from "lucide-react";

const TopSection = ({ band }: { band: Band }) => (
  <div className="flex flex-col md:flex-row items-center md:items-start gap-[1rem] justify-between">
    <div className="flex flex-col gap-[1rem]">
      <Card>
        <CardHeader>
          <CardTitle>{band.name}</CardTitle>
          <CardDescription>Insert City Hardcore</CardDescription>
        </CardHeader>
        <CardContent>
          {band.name && (
            <div className="relative">
              <Image
                className="lg:ml-auto xl:ml-auto rounded-sm"
                alt={band.name}
                src={faker.image.urlLoremFlickr({ category: 'people' })}
                width={250}
                height={250}
                priority
              />
            </div>
          )}
        </CardContent>
        <CardFooter>
          <div className="flex flex-col gap-1 w-full">
            <Link href={{ pathname: "/edit/band", query: { id: band.id } }}>
              <Button className="w-full">Edit Band</Button>
            </Link>
            <Link href={{ pathname: "/create/release", query: { band_id: band.id } }}>
              <Button className="w-full">Add Release</Button>
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  </div>
);

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

  return (
    <main className="py-[1rem] flex-col">
      <Header />
      <div className="py-[1rem] w-full">
        <Separator />
      </div>
      {band && (
        <div className="flex flex-col md:flex-row gap-[1rem] p-[4]">
          <TopSection band={band} />
          <Tabs defaultValue="discography" className="w-full">
            <TabsList>
              <TabsTrigger value="discography">Discography</TabsTrigger>
              <TabsTrigger value="members">Members</TabsTrigger>
              <TabsTrigger value="similar-artists">Similar Artists</TabsTrigger>
              <TabsTrigger value="links">Links</TabsTrigger>
            </TabsList>
            <TabsContent className="w-full" value="discography">
              <DiscographyTable
                band={band.name}
                releases={band.releases ?? []}
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

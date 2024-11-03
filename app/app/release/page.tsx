'use client'

import Image from "next/image";
import { Button } from "@/components/ui/button";
// import { NavigationMenuDemo } from "./nav";
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Release } from "@/lib/types";
import { TracksTable } from "./table";
import { faker } from "@faker-js/faker";
import { AlbumBreadcrumbs } from "./breadcrumbs";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const SearchInput = () => (
  <Input type="search" placeholder="Search..." />
);

// const RecentAdditions = () => {
//   return (
//     <div className="flex-1">
//       <span className="text-4xl">Recent Additions</span>
//       {ra.map((a, i) => {
//         return (
//           <div className="flex flex-row gap-[1rem]" key={i}>
//             <span>{a.name}</span>
//             <span>by - {a.submitter}</span>
//           </div>
//         )
//       })}
//     </div>
//   )
// }

// const RecentUpdates = () => {
//   const router = useRouter();
//   const pathname = usePathname();

//   const addQueryParam = (name: string) => {
//       const params = new URLSearchParams();
//       params.set("name", name);
//       router.replace(`/band?${params.toString()}`);
//   };
//   return (
//     <div className="flex-1">
//       <span className="text-4xl">Recent Updates</span>
//       {ru.map((u, i) => {
//         return (
//           <div className="flex flex-row gap-[1rem]" key={i}>
//             <a onClick={() => addQueryParam(u.name)}>{u.name}</a>
//             <span>by - {u.submitter}</span>
//           </div>
//         );
//       })}
//     </div>
//   )
// }

// const RecentReviews = () => {
//   return (
//     <div className="flex-1">
//       <span className="text-4xl">Recent Reviews</span>
//       {rr.map((r, i) => {
//         return (
//           <div className="flex flex-row gap-[1rem]" key={i}>
//             <span className="italic">{r.album}</span>
//             <span>"{r.name}"</span>
//             <span>by - {r.reviewer}</span>
//           </div>
//         )
//       })}
//     </div>
//   )
// }

const AlbumLink = (props: {
  name: string;
  id: string;
}) => (
  <Link
    className="hover:underline"
    href={{
      pathname: "/album",
      query: {
        name: props.name,
        id: props.id
      }
    }}
  >
    {props.name}
  </Link>
)

export default function Album() {
  const [release, setRelease] = useState<Release | null>(null)
  const searchParams = useSearchParams();
  const name = searchParams.get("name")

  useEffect(() => {
    const id = Number(searchParams.get("id"));

    const fetchData = async (params: { id: number }) => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URI}/release/${params.id}`);

      return res.json();
    }

    if (id !== null) {
      fetchData({ id }).then((res: Release[]) =>{
        console.log(res)
        setRelease(res[0]);
      })
    }
  }, [])

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
      <div className="flex flex-col gap-[1rem] p-[1rem]">
        { release && (
          <AlbumBreadcrumbs
            band={release?.band_name}
            name={release?.name}
            id={release.band_id}
          />
        )}
        { release && (
          <div className="flex flex-col gap-[1rem] p-[1rem]">
            <div className="flex flex-row">
              <div className="flex flex-col gap-[1rem]">
                <span className="text-4xl">{release?.name}</span>
                <Link
                  className="hover:underline"
                  href={{
                    pathname: '/band',
                    query: {
                      name: release.band_name,
                      id: release.band_id
                    }
                  }}
                >
                  {release.band_name}
                </Link>
              </div>
              { release.name && (
                <img
                  className="ml-auto"
                  alt={release.name}
                  src={faker.image.urlLoremFlickr({ category: 'people' })}
                  width={250}
                  height={250}
                />
              )}
            </div>
            <Tabs defaultValue="discography">
              <TabsList>
                <TabsTrigger value="tracks">Tracks</TabsTrigger>
                <TabsTrigger value="lineup">Linueup</TabsTrigger>
                <TabsTrigger value="reviews">Reviews</TabsTrigger>
                <TabsTrigger value="other">Other</TabsTrigger>
              </TabsList>
              <TabsContent className="w-full" value="tracks">
                { release && <TracksTable tracks={release.tracks ?? []} /> }
              </TabsContent>
              {/* <TabsContent value="members">
                <MemberTable band={band.name} members={band.members} />
              </TabsContent> */}
              {/* <TabsContent value="similar-artists">
                <SimilarArtistsTable band={band.name} albums={band.discography} />
              </TabsContent>
              <TabsContent value="links">
                { band.name && <LinksTable band={band.name} albums={band.discography} /> }
              </TabsContent> */}
            </Tabs>
          </div>
        )
      }
      </div>
    </main>
  );
}

'use client'

import { Separator } from "@/components/ui/separator";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Release } from "@/lib/types";
import { TracksTable } from "./table";
import { faker } from "@faker-js/faker";
import { AlbumBreadcrumbs } from "./breadcrumbs";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Header } from "@/components/ui/header";
import Image from "next/image";
import { TopSection } from "@/components/TopSection";

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

  console.log(release)

  useEffect(() => {
    const id = Number(searchParams.get("id"));

    const fetchData = async (params: { id: number }) => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URI}:${process.env.NEXT_PUBLIC_API_PORT}/release/${params.id}`);

      return res.json();
    }

    if (id !== null) {
      fetchData({ id }).then((res) => setRelease(res));
    }
  }, [searchParams])

  return (
    <main className="py-[1rem] flex-col border border-red-500">
      <Header />
      <div className="py-[1rem] w-full">
        <Separator />
      </div>
      <div className="flex flex-col gap-[1rem] p-[1rem] border border-red-500">
        { release && (
          <AlbumBreadcrumbs
            band={release?.band.name}
            name={release?.name}
            id={release.band_id}
          />
        )}
        { release && (
          <div className="flex flex-col md:flex-row gap-[1rem] p-4 border border-red-500">
            { release && <TopSection id={release.band_id} name={release.band.name} /> }
            <Tabs defaultValue="discography" className="w-full border border-red-500 p-4">
              <TabsList>
                <TabsTrigger value="tracks">Tracks</TabsTrigger>
                <TabsTrigger value="lineup">Lineup</TabsTrigger>
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

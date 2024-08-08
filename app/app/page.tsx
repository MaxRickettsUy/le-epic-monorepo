'use client'

import Image from "next/image";
import { Button } from "@/components/ui/button";
import { NavigationMenuDemo } from "./nav";
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Artist } from "@/lib/types";

const SearchInput = () => (
  <Input type="search" placeholder="Search..." />
);

// const RecentAdditions = () => {
//   return (
//     <div className="flex-1">
//       <span className="text-4xl">Recent Additions</span>
//       {ra.map((a, i) => {
//         return (
//           <div className="flex flex-row" key={i}>
//             <Link className="hover:underline" href={{ pathname: "/band", query: { name: a.name } }}>{a.name}</Link>
//             <span>- {a.submitter}</span>
//           </div>
//         )
//       })}
//     </div>
//   )
// }

// const RecentUpdates = () => {
//   return (
//     <div className="flex-1">
//       <span className="text-4xl">Recent Updates</span>
//       {ru.map((u, i) => {
//         return (
//           <div className="flex flex-row gap-[4px]" key={i}>
//             <Link className="hover:underline" href={{ pathname: "/band", query: {name: u.name } }}>{u.name}</Link>
//             <span>- {u.submitter}</span>
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
//       <div className="flex flex-col gap-[4px]">
//         {rr.map((r, i) => {
//           return (
//             <div className="flex flex-col md:flex-row lg:flex-row xl:flex-row gap-[8px]" key={i}>
//               <Link className="italic hover:underline" href={{ pathname: "/album", query: {name: r.album } }}>{r.album}</Link>
//               <span>|</span>
//               <span>"{r.name}" - {r.reviewer}</span>
//             </div>
//           )
//         })}
//       </div>
//     </div>
//   )
// }

const ArtistLink = (props: { name: string }) => (
  <Link
    className="hover:underline"
    href={{
      pathname: "/band",
      query: {
        name: props.name
      }
    }}
  >
    {props.name}
  </Link>
)

export default function Home() {
  const [artists, setArtists] = useState<Artist[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      const response = await fetch('/api/home');

      return response.json()
    }

    fetchData().then((res) => {
      setArtists(res.artists)
    })
  }, [])

  return (
    <main className="py-[1rem] flex-col">
      <div className="flex flex-row gap-[1rem] px-[1rem]">
        <Avatar>
          <AvatarFallback>L</AvatarFallback>
        </Avatar>
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
      <div className="flex flex-col md:flex-row lg:flex-row xl:flex-row gap-[1rem] p-[1rem]">
        <div className="flex flex-col">
          {
            artists.map((a) => (
              <ArtistLink name={a.name} />
            ))
          }
        </div>
        {/* <RecentAdditions />
        <RecentUpdates />
        <RecentReviews /> */}
      </div>
    </main>
  );
}

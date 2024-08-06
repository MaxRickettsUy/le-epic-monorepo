import Image from "next/image";
import { Button } from "@/components/ui/button";
import { NavigationMenuDemo } from "./nav";
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface Addition {
  type: "band" | "album";
  name: string;
  submitter: string;
}

interface Update {
  type: "band" | "album";
  name: string;
  submitter: string;
}

interface Review {
  album: string;
  name: string;
  reviewer: string;
}

const ra: Addition[] = [
  {type: "band", name: "Contention", submitter: "Test" },
  {type: "band", name: "Contention", submitter: "Test" },
  {type: "band", name: "Contention", submitter: "Test" },
  {type: "band", name: "Contention", submitter: "Test" },
  {type: "band", name: "Contention", submitter: "Test" },
  {type: "band", name: "Contention", submitter: "Test" },
]

const ru: Update[] = [
  {type: "band", name: "Rude Awakening", submitter: "Test"},
  {type: "band", name: "Rude Awakening", submitter: "Test"},
  {type: "band", name: "Rude Awakening", submitter: "Test"},
  {type: "band", name: "Rude Awakening", submitter: "Test"},
  {type: "band", name: "Rude Awakening", submitter: "Test"},
  {type: "band", name: "Rude Awakening", submitter: "Test"},
]

const rr: Review[] = [
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
  {album: "One With the Underdogs", name: "Classic", reviewer: "Test"},
]

const SearchInput = () => (
  <Input type="search" placeholder="Search..." />
);

const RecentAdditions = () => {
  return (
    <div className="flex-1">
      <span className="text-4xl">Recent Additions</span>
      {ra.map((a, i) => {
        return (
          <div className="flex flex-row gap-[1rem]" key={i}>
            <span>{a.name}</span>
            <span>by - {a.submitter}</span>
          </div>
        )
      })}
    </div>
  )
}

const RecentUpdates = () => {
  return (
    <div className="flex-1">
      <span className="text-4xl">Recent Updates</span>
      {ru.map((u, i) => {
        return (
          <div className="flex flex-row gap-[1rem]" key={i}>
            <span>{u.name}</span>
            <span>by - {u.submitter}</span>
          </div>
        );
      })}
    </div>
  )
}

const RecentReviews = () => {
  return (
    <div className="flex-1">
      <span className="text-4xl">Recent Reviews</span>
      {rr.map((r, i) => {
        return (
          <div className="flex flex-row gap-[1rem]" key={i}>
            <span className="italic">{r.album}</span>
            <span>{r.name}</span>
            <span>by - {r.reviewer}</span>
          </div>
        )
      })}
    </div>
  )
}

export default function Home() {
  return (
    <main className="py-[1rem] flex-col">
      <div className="flex flex-row gap-[1rem] px-[1rem]">
        <Avatar>
          <AvatarFallback>L</AvatarFallback>
        </Avatar>
        <NavigationMenuDemo />
        <div className="ml-auto">
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
        <RecentAdditions />
        <RecentUpdates />
        <RecentReviews />
      </div>
    </main>
  );
}

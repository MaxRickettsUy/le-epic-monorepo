import Image from "next/image";
import { Button } from "@/components/ui/button";
import { NavigationMenuDemo } from "./nav";
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const SearchInput = () => (
  <Input type="search" placeholder="Search..." />
);

export default function Home() {
  return (
    <main className="p-[1rem] flex-col">
      <div className="flex flex-row gap-[1rem]">
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
    </main>
  );
}

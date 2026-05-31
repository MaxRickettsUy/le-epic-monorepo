import Link from "next/link";
import { Avatar, AvatarFallback } from "./avatar";
import { Input } from "./input";

const SearchInput = () => (
  <form action="/search" method="get" role="search">
    <label htmlFor="catalog-search" className="sr-only">
      Search the catalog
    </label>
    <Input id="catalog-search" name="q" type="search" placeholder="Search bands & albums..." />
  </form>
);

export const Header = () => {
  return (
    <header className="sticky top-0 z-50 flex flex-row items-center gap-[1rem] bg-header px-[1rem] py-2">
      <Link href="/" aria-label="le-epic home">
        <Avatar>
          <AvatarFallback>L</AvatarFallback>
        </Avatar>
      </Link>
      <nav aria-label="Primary" className="ml-auto flex flex-row items-center gap-[1rem]">
        <Link href="/bands" className="text-sm font-medium hover:underline">
          Browse
        </Link>
        <SearchInput />
      </nav>
      <Avatar>
        <AvatarFallback>U</AvatarFallback>
      </Avatar>
    </header>
  );
};

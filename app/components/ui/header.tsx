import Link from "next/link";
import { Avatar, AvatarFallback } from "./avatar";
import { Button } from "./button";
import { Input } from "./input";
import { ThemeToggle } from "./theme-toggle";

const SearchInput = () => (
  <>
    <label htmlFor="catalog-search" className="sr-only">
      Search the catalog
    </label>
    <Input id="catalog-search" type="search" placeholder="Search..." />
  </>
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
        <Button asChild className="hidden sm:inline-flex">
          <Link href="/create/band">Add Band</Link>
        </Button>
        <SearchInput />
        <ThemeToggle />
      </nav>
      <Avatar>
        <AvatarFallback>U</AvatarFallback>
      </Avatar>
    </header>
  );
};

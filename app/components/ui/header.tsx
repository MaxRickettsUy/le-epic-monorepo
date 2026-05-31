import Link from "next/link";
import { Avatar, AvatarFallback } from "./avatar";
import { Input } from "./input";
import { MobileMenu } from "./mobile-menu";

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
      <nav
        aria-label="Primary"
        className="ml-auto hidden flex-row items-center gap-[1rem] md:flex"
      >
        <Link href="/bands" className="text-sm font-medium hover:underline">
          Browse
        </Link>
        <SearchInput />
      </nav>
      <Avatar className="ml-auto md:ml-0">
        <AvatarFallback>U</AvatarFallback>
      </Avatar>
      <div className="md:hidden">
        <MobileMenu />
      </div>
    </header>
  );
};

import Link from "next/link";
import { Avatar, AvatarFallback } from "./avatar";
import { Button } from "./button";
import { Input } from "./input";

const SearchInput = () => <Input type="search" placeholder="Search..." />;

export const Header = () => {
  return (
    <div className="flex flex-row gap-[1rem] px-[1rem]">
      <Link href={"/"}>
        <Avatar>
          <AvatarFallback>L</AvatarFallback>
        </Avatar>
      </Link>
      <div className="ml-auto flex flex-row gap-[1rem]">
        <Button asChild>
          <Link href="/create/band">Add Band</Link>
        </Button>
        <SearchInput />
      </div>
      <Avatar>
        <AvatarFallback>U</AvatarFallback>
      </Avatar>
    </div>
  );
};

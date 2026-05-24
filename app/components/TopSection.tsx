import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card";
import Link from "next/link";
import { Button } from "./ui/button";

export const TopSection = (props: { id: number; name: string; picture?: string | null }) => {
  return (
    <div className="flex flex-col items-center justify-between gap-[1rem] md:flex-row md:items-start">
      <div className="flex flex-col gap-[1rem]">
        <Card>
          <CardHeader>
            <CardTitle>{props.name}</CardTitle>
            <CardDescription>Insert City Hardcore</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Real artwork is wired up in Phase 4 (next/image + remote hosts). */}
            <div
              className="flex h-[250px] w-[250px] items-center justify-center rounded-sm bg-muted text-4xl font-bold text-muted-foreground"
              aria-label={props.name}
            >
              {props.name.charAt(0).toUpperCase()}
            </div>
          </CardContent>
          <CardFooter>
            <div className="flex w-full flex-col gap-1">
              <Link href={`/edit/band/${props.id}`}>
                <Button className="w-full">Edit Band</Button>
              </Link>
              <Link href={`/create/release/${props.id}`}>
                <Button className="w-full">Add Release</Button>
              </Link>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

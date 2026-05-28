import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card";
import Link from "next/link";
import Image from "next/image";
import { Button } from "./ui/button";
import { GenreBadges } from "./GenreBadges";
import type { Genre } from "@/lib/types";

function yearsActive(beginYear?: number | null, endYear?: number | null): string | null {
  if (beginYear == null && endYear == null) return null;
  if (beginYear == null) return `until ${endYear}`;
  return `${beginYear}–${endYear ?? "present"}`;
}

export const TopSection = (props: {
  id: number;
  name: string;
  picture?: string | null;
  genres?: Genre[];
  beginYear?: number | null;
  endYear?: number | null;
}) => {
  const active = yearsActive(props.beginYear, props.endYear);
  return (
    <div className="flex flex-col items-center justify-between gap-[1rem] md:flex-row md:items-start">
      <div className="flex flex-col gap-[1rem]">
        <Card>
          <CardHeader>
            <CardTitle>{props.name}</CardTitle>
            <CardDescription>Insert City Hardcore</CardDescription>
            {props.genres && props.genres.length > 0 && (
              <GenreBadges genres={props.genres} className="flex flex-wrap gap-1.5 pt-1" />
            )}
          </CardHeader>
          <CardContent>
            {props.picture ? (
              <Image
                src={props.picture}
                alt={`${props.name} artwork`}
                width={250}
                height={250}
                className="h-[250px] w-[250px] rounded-sm object-cover"
              />
            ) : (
              <div
                className="flex h-[250px] w-[250px] items-center justify-center rounded-sm bg-muted text-4xl font-bold text-muted-foreground"
                role="img"
                aria-label={`${props.name} (no artwork)`}
              >
                {props.name.charAt(0).toUpperCase()}
              </div>
            )}
            {active && <p className="mt-2 text-sm text-muted-foreground">Active {active}</p>}
          </CardContent>
          <CardFooter>
            <div className="flex w-full flex-col gap-1">
              <Button className="w-full" asChild>
                <Link href={`/edit/band/${props.id}`}>Edit Band</Link>
              </Button>
              <Button className="w-full" asChild>
                <Link href={`/create/release/${props.id}`}>Add Release</Link>
              </Button>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

import { Fragment } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatDuration } from "@/lib/format";
import type { ReleaseDetail } from "@/lib/types";

function sumTrackLengths(tracks: ReleaseDetail["tracks"]): number | null {
  const lengths = tracks.map((t) => t.length).filter((l): l is number => l != null);
  if (lengths.length === 0) return null;
  return lengths.reduce((a, b) => a + b, 0);
}

export function ReleaseHeader({ release }: { release: ReleaseDetail }) {
  // Prefer the stored album length; otherwise total the tracks we have.
  const runtime = release.length ?? sumTrackLengths(release.tracks);
  const kind = release.type ?? release.release_type;

  const facts = [
    kind && { label: "Type", value: kind },
    release.year && { label: "Year", value: String(release.year) },
    release.label && { label: "Label", value: release.label },
    runtime && { label: "Runtime", value: formatDuration(runtime) },
  ].filter(Boolean) as { label: string; value: string }[];

  return (
    <div className="flex flex-col items-center gap-[1rem] md:flex-row md:items-start">
      <Card>
        <CardHeader>
          <CardTitle>{release.name}</CardTitle>
          <CardDescription>
            by{" "}
            <Link href={`/band/${release.band_id}`} className="hover:underline">
              {release.band.name}
            </Link>
          </CardDescription>
        </CardHeader>
        <CardContent>
          {release.art ? (
            <Image
              src={release.art}
              alt={`${release.name} cover art`}
              width={250}
              height={250}
              className="h-[250px] w-[250px] rounded-sm object-cover"
            />
          ) : (
            <div
              className="flex h-[250px] w-[250px] items-center justify-center rounded-sm bg-muted text-4xl font-bold text-muted-foreground"
              role="img"
              aria-label={`${release.name} (no cover art)`}
            >
              {release.name.charAt(0).toUpperCase()}
            </div>
          )}
          {facts.length > 0 && (
            <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
              {facts.map((f) => (
                <Fragment key={f.label}>
                  <dt className="text-muted-foreground">{f.label}</dt>
                  <dd className="font-medium">{f.value}</dd>
                </Fragment>
              ))}
            </dl>
          )}
        </CardContent>
        <CardFooter>
          <Button className="w-full" asChild>
            <Link href={`/edit/release/${release.id}`}>Edit Release</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}

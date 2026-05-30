import Link from "next/link";
import Image from "next/image";
import { Card } from "@/components/ui/card";
import type { ReleaseListItem } from "@/lib/types";

/** Compact album tile for discovery grids: art (or initial fallback) + album + band/year. */
export const AlbumCard = ({ release }: { release: ReleaseListItem }) => {
  return (
    <Link href={`/release/${release.id}`} className="group">
      <Card className="overflow-hidden transition-shadow hover:shadow-md">
        <div className="relative aspect-square w-full bg-muted">
          {release.art ? (
            <Image
              src={release.art}
              alt={`${release.name} cover art`}
              fill
              sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 20vw"
              className="object-cover"
            />
          ) : (
            <div
              className="flex h-full w-full items-center justify-center text-5xl font-bold text-muted-foreground"
              role="img"
              aria-label={`${release.name} (no cover art)`}
            >
              {release.name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        <div className="p-3">
          <p className="truncate font-medium group-hover:underline" title={release.name}>
            {release.name}
          </p>
          <p className="truncate text-sm text-muted-foreground">
            {release.band_name}
            {release.year ? ` · ${release.year}` : ""}
          </p>
        </div>
      </Card>
    </Link>
  );
};

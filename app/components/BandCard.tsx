import Link from "next/link";
import Image from "next/image";
import { Card } from "./ui/card";
import { GenreBadges } from "./GenreBadges";
import type { BandListItem } from "@/lib/types";

/** Compact band tile for the landing grid: artwork (or initial fallback) + name. */
export const BandCard = ({ band }: { band: BandListItem }) => {
  // Prefer the logo; fall back to the band photo, then an initial-letter tile.
  const image = band.logo ?? band.band_picture;
  return (
    <Link href={`/band/${band.id}`} className="group">
      <Card className="overflow-hidden transition-shadow hover:shadow-md">
        <div className="relative aspect-square w-full bg-muted">
          {image ? (
            <Image
              src={image}
              alt={`${band.name} artwork`}
              fill
              sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 20vw"
              className="object-cover"
            />
          ) : (
            <div
              className="flex h-full w-full items-center justify-center text-5xl font-bold text-muted-foreground"
              role="img"
              aria-label={`${band.name} (no artwork)`}
            >
              {band.name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        <div className="p-3">
          <p className="truncate font-medium group-hover:underline" title={band.name}>
            {band.name}
          </p>
          <p className="truncate text-sm text-muted-foreground">{band.location || band.country}</p>
          <GenreBadges genres={band.genres} limit={2} className="mt-2 flex flex-wrap gap-1" />
        </div>
      </Card>
    </Link>
  );
};

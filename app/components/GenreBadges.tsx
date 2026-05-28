import { Badge } from "./ui/badge";
import type { Genre } from "@/lib/types";

/**
 * Renders a band's curated sub-genres as badges. Genres arrive strongest-voted
 * first; pass `limit` to show only the top N (e.g. 1–2 on compact tiles).
 * Renders nothing when the band has no genres.
 */
export const GenreBadges = ({
  genres,
  limit,
  className,
}: {
  genres: Genre[];
  limit?: number;
  className?: string;
}) => {
  const shown = limit !== undefined ? genres.slice(0, limit) : genres;
  if (shown.length === 0) return null;
  return (
    <div className={className ?? "flex flex-wrap gap-1.5"}>
      {shown.map((g) => (
        <Badge key={g.slug} variant="secondary">
          {g.name}
        </Badge>
      ))}
    </div>
  );
};

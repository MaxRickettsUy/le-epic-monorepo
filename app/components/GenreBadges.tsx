import Link from "next/link";
import { Badge } from "./ui/badge";
import type { Genre } from "@/lib/types";

/**
 * Renders a band's curated sub-genres as badges linking to the faceted
 * `/bands?genre=<slug>` index. Genres arrive strongest-voted first; pass
 * `limit` to show only the top N (e.g. 1–2 on compact tiles). Renders
 * nothing when the band has no genres.
 *
 * Set `asLinks={false}` when rendering inside an enclosing `<Link>` (e.g. a
 * clickable search-result row) — nested `<a>` tags are invalid HTML and
 * trigger a hydration error.
 */
export const GenreBadges = ({
  genres,
  limit,
  className,
  asLinks = true,
}: {
  genres: Genre[];
  limit?: number;
  className?: string;
  asLinks?: boolean;
}) => {
  const shown = limit !== undefined ? genres.slice(0, limit) : genres;
  if (shown.length === 0) return null;
  return (
    <div className={className ?? "flex flex-wrap gap-1.5"}>
      {shown.map((g) =>
        asLinks ? (
          <Link key={g.slug} href={`/bands?genre=${encodeURIComponent(g.slug)}`}>
            <Badge variant="secondary" className="hover:bg-secondary/80">
              {g.name}
            </Badge>
          </Link>
        ) : (
          <Badge key={g.slug} variant="secondary">
            {g.name}
          </Badge>
        ),
      )}
    </div>
  );
};

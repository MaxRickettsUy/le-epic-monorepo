import Link from "next/link";
import { allowlistBandAction } from "@/app/actions";
import { listNeedsReview } from "@/lib/api";
import { Header } from "@/components/ui/header";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { GenreBadges } from "@/components/GenreBadges";
import type { MbTag } from "@/lib/types";

const MAX_INLINE_TAGS = 5;

function MbTagList({ tags }: { tags: MbTag[] | null | undefined }) {
  if (tags == null) return <span className="text-muted-foreground">—</span>;
  if (tags.length === 0) return <span className="text-muted-foreground">no MB tags</span>;
  const head = tags.slice(0, MAX_INLINE_TAGS);
  const rest = tags.length - head.length;
  return (
    <div
      className="flex flex-wrap gap-1"
      title={tags.map((t) => `${t.name} (${t.votes})`).join(", ")}
    >
      {head.map((tag) => (
        <Badge key={tag.name} variant="outline" className="font-normal">
          {tag.name}
          <span className="ml-1 text-muted-foreground tabular-nums">{tag.votes}</span>
        </Badge>
      ))}
      {rest > 0 && <span className="self-center text-xs text-muted-foreground">+{rest} more</span>}
    </div>
  );
}

export const metadata = { title: "Needs review" };
// Always fresh: this view is a curation tool, not a public catalogue page.
export const fetchCache = "force-no-store";

interface PageProps {
  searchParams: Promise<{ include_resolved?: string }>;
}

function formatShare(share: number | null | undefined, total: number | null | undefined): string {
  if (total == null || total === 0) return "no MB tags";
  if (share == null) return "—";
  return `${Math.round(share * 100)}%`;
}

export default async function NeedsReviewPage({ searchParams }: PageProps) {
  const { include_resolved } = await searchParams;
  const includeResolved = include_resolved === "true";
  const bands = await listNeedsReview({ includeResolved });

  return (
    <main className="flex flex-col pb-[1rem]">
      <Header />
      <div className="flex flex-col gap-4 p-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-bold">Needs review</h1>
          <p className="text-sm text-muted-foreground">
            Bands the seed auto-flagged as likely off-genre. These are hidden from the public
            listing until you decide: <strong>Allowlist</strong> to vouch for the band (clears the
            flag, sticky across re-seeds), or delete it (records the MBID in the blacklist so the
            seed won&rsquo;t bring it back). Ranked by lowest seed-share first.
          </p>
        </div>

        <div className="flex items-center gap-3 text-sm">
          <Link
            href={includeResolved ? "?" : "?include_resolved=true"}
            className="underline hover:no-underline"
          >
            {includeResolved ? "Hide allowlisted" : "Show allowlisted too"}
          </Link>
          <span className="text-muted-foreground">{bands.length} shown</span>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Band</TableHead>
              <TableHead>Country</TableHead>
              <TableHead>Sub-genres</TableHead>
              <TableHead>MB tags (top {MAX_INLINE_TAGS})</TableHead>
              <TableHead>Seed share</TableHead>
              <TableHead>Votes</TableHead>
              <TableHead>Reviewed?</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {bands.map((band) => (
              <TableRow key={band.id}>
                <TableCell className="font-medium">
                  <div className="flex items-center gap-2">
                    <Link href={`/band/${band.id}`} className="hover:underline">
                      {band.name}
                    </Link>
                    {band.mbid && (
                      <a
                        href={`https://musicbrainz.org/artist/${band.mbid}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-muted-foreground underline hover:no-underline"
                        title="Open on MusicBrainz"
                      >
                        MB&nbsp;↗
                      </a>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">{band.country || "—"}</TableCell>
                <TableCell>
                  {band.genres.length > 0 ? (
                    <GenreBadges genres={band.genres} className="flex flex-wrap gap-1" />
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell>
                  <MbTagList tags={band.mb_tags} />
                </TableCell>
                <TableCell>{formatShare(band.seed_share, band.total_tag_votes)}</TableCell>
                <TableCell className="text-muted-foreground">
                  {band.seed_votes ?? 0}/{band.total_tag_votes ?? 0}
                </TableCell>
                <TableCell>
                  {band.allowlisted_at ? (
                    <Badge variant="secondary">Allowlisted</Badge>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-3">
                    {!band.allowlisted_at && (
                      <form action={allowlistBandAction.bind(null, band.id)}>
                        <button
                          type="submit"
                          className="underline hover:no-underline"
                          title="Clear the auto-flag and mark this band as vouched-for"
                        >
                          Allowlist
                        </button>
                      </form>
                    )}
                    <Link href={`/edit/band/${band.id}`} className="underline hover:no-underline">
                      Edit
                    </Link>
                  </div>
                </TableCell>
              </TableRow>
            ))}
            {bands.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-muted-foreground">
                  Nothing to review.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </main>
  );
}

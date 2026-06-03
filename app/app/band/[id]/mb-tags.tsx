import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { MbTag } from "@/lib/types";

interface MbTagsTableProps {
  tags: MbTag[] | null | undefined;
  seedVotes: number | null | undefined;
  totalVotes: number | null | undefined;
  seedShare: number | null | undefined;
}

export const MbTagsTable = ({ tags, seedVotes, totalVotes, seedShare }: MbTagsTableProps) => {
  if (tags === null || tags === undefined) {
    return (
      <p className="p-4 text-sm text-muted-foreground">
        No MusicBrainz tag snapshot for this band. Re-run the seed to populate it.
      </p>
    );
  }

  if (tags.length === 0) {
    return (
      <p className="p-4 text-sm text-muted-foreground">
        MusicBrainz has no tags for this band.
      </p>
    );
  }

  const sharePct = seedShare != null ? `${Math.round(seedShare * 100)}%` : "—";

  return (
    <div className="flex flex-col gap-2">
      <p className="px-1 text-xs text-muted-foreground">
        Raw MusicBrainz tag votes captured at seed time. Curated sub-genres come from
        intersecting this list with the project&apos;s genre vocabulary, so tags missing
        from that vocabulary (e.g. metal subgenres) are dropped before sub-genres are
        assigned. Hardcore-punk share: <span className="font-medium">{sharePct}</span>{" "}
        ({seedVotes ?? 0}/{totalVotes ?? 0}).
      </p>
      <div className="max-h-[60vh] overflow-y-auto">
        <Table>
          <TableHeader className="sticky top-0 z-10 bg-background">
            <TableRow>
              <TableHead>Tag</TableHead>
              <TableHead className="w-24 text-right">Votes</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tags.map((tag, index) => (
              <TableRow key={`${tag.name}-${index}`}>
                <TableCell className="font-medium">{tag.name}</TableCell>
                <TableCell className="text-right tabular-nums">{tag.votes}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { SimilarBand } from "@/lib/types";
import Link from "next/link";

/** Human-readable reasons a band matched, derived from the scoring factors. */
function matchReasons(band: SimilarBand): string[] {
  const reasons: string[] = [];
  if (band.shared_members > 0) {
    reasons.push(
      `${band.shared_members} shared member${band.shared_members > 1 ? "s" : ""}`,
    );
  }
  if (band.same_location) reasons.push("Same scene");
  if (band.same_label) reasons.push("Same label");
  // Country is redundant with a same-scene match; only show it on its own.
  if (band.same_country && !band.same_location) reasons.push("Same country");
  return reasons;
}

export const SimilarArtistsTable = ({ bands }: { bands: SimilarBand[] }) => {
  if (bands.length === 0) {
    return <p className="p-4 text-sm text-muted-foreground">No similar artists found yet.</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Location</TableHead>
          <TableHead>Why</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {bands.map((band) => (
          <TableRow key={band.id}>
            <TableCell className="font-medium">
              <Link className="hover:underline" href={`/band/${band.id}`}>
                {band.name}
              </Link>
            </TableCell>
            <TableCell>{band.location || "—"}</TableCell>
            <TableCell>
              <div className="flex flex-wrap gap-1">
                {matchReasons(band).map((reason) => (
                  <Badge key={reason} variant="secondary">
                    {reason}
                  </Badge>
                ))}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { SimilarBand } from "@/lib/types";
import Link from "next/link";

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
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

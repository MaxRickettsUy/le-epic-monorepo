import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Release } from "@/lib/types";
import Link from "next/link";

const ReleaseLink = ({ release }: { release: Release }) => (
  <Link
    className={`hover:underline ${release.release_type === "lp" ? "font-bold" : ""}`}
    href={`/release/${release.id}`}
  >
    {release.name}
  </Link>
);

export const DiscographyTable = ({ releases }: { releases: Release[] }) => {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-100">Year</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Rating</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {releases.map((release) => (
          <TableRow key={release.id}>
            <TableCell className="font-medium">{release.year}</TableCell>
            <TableCell>
              <ReleaseLink release={release} />
            </TableCell>
            <TableCell>{release.release_type?.toUpperCase()}</TableCell>
            <TableCell>
              {release.review_count > 0
                ? `${release.avg_review}% (${release.review_count} reviews)`
                : "—"}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

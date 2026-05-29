import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Track } from "@/lib/types";
import { formatDuration } from "@/lib/format";

export const TracksTable = ({ tracks }: { tracks: Track[] }) => {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[500px]">Name</TableHead>
          <TableHead className="w-[100px]">Length</TableHead>
          <TableHead className="w-[100px]">Lyrics</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tracks.map((track) => (
          <TableRow key={track.id}>
            <TableCell className="font-medium">{track.name}</TableCell>
            <TableCell>{formatDuration(track.length)}</TableCell>
            <TableCell>{track.lyrics ? "Yes" : ""}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

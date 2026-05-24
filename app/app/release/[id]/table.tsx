import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Track } from "@/lib/types";

const formatLength = (seconds?: number | null) => {
  if (seconds == null) return "";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

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
            <TableCell>{formatLength(track.length)}</TableCell>
            <TableCell>{track.lyrics ? "Yes" : ""}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Song, Track } from "@/lib/types"
import { faker } from "@faker-js/faker";

interface Props {
  tracks: Track[];
}

export const TracksTable = (props: Props) => {
  return (
    <Table>
      {/* <TableCaption>A list of your recent invoices.</TableCaption> */}
      <TableHeader>
        <TableRow>
          <TableHead className="w-[500px]">Name</TableHead>
          <TableHead className="w-[100px]">Length</TableHead>
          <TableHead className="w-[100px]">Lyrics</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        { props.tracks.map((track) => (
          <TableRow key={track.name}>
            <TableCell className="font-medium">{track.name}</TableCell>
            <TableCell>{track.length}</TableCell>
          </TableRow>
        ))}
      </TableBody>
      {/* <TableFooter>
        <TableRow>
          <TableCell colSpan={3}>Total</TableCell>
          <TableCell className="text-right">$2,500.00</TableCell>
        </TableRow>
      </TableFooter> */}
    </Table>
  )
}

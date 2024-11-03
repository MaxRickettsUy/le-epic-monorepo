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
import { Release } from "@/lib/types"
import { faker } from "@faker-js/faker";
import Link from "next/link";

interface Props {
  albums: Release[];
  band: string;
}

const AlbumLink = (props: { name: string, band: string }) => (
  <Link
    className="hover:underline"
    href={{
      pathname: "/album",
      query: { name: props.name, band: props.band }
    }}
  >
    {props.name}
  </Link>
)

export const LinksTable =(props: Props) => {
  return (
    <Table>
      {/* <TableCaption>A list of your recent invoices.</TableCaption> */}
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Year</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Rating</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {props.albums.map((album) => (
          <TableRow key={album.name}>
            <TableCell className="font-medium">{album.year}</TableCell>
            <TableCell>
              <AlbumLink
                band={album.bandName}
                name={album.name}
              />
            </TableCell>
            { album.reviewCount > 0 && (
              <TableCell>
                {album.rating}% ({album.reviewCount} reviews)
              </TableCell>
            )}
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

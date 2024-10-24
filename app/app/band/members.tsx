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
import { Album, Member } from "@/lib/types"
import { faker } from "@faker-js/faker";
import Link from "next/link";

interface Props {
  members: Member[];
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

export const MemberTable =(props: Props) => {
  return (
    <Table>
      {/* <TableCaption>A list of your recent invoices.</TableCaption> */}
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Role</TableHead>
          <TableHead>Other Bands</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {props.members.map((member) => (
          <TableRow key={member.name}>
            <TableCell className="font-medium">{member.name}</TableCell>
            <TableCell>{member.role}</TableCell>
            <TableCell>insert other bands</TableCell>
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

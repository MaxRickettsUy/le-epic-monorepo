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

const ReleaseLink = (props: { release: Release }) => {
  return (
    <Link
      className={`hover:underline ${props.release.release_type === "lp" ? 'font-bold' : ''}`}
      href={{
        pathname: "/release",
        query: {
          id: props.release.id
        }
      }}
    >
      {props.release.name}
    </Link>
  )
};

export const DiscographyTable = (props: {
  band: string;
  releases: Release[];
}) => {
  console.log(props.releases)

  return (
    <Table>
      {/* <TableCaption>A list of your recent invoices.</TableCaption> */}
      <TableHeader>
        <TableRow>
          <TableHead className="w-100">Year</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Rating</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {props.releases.map((release, i) => (
          <TableRow key={i}>
            <TableCell className="font-medium">{release.year}</TableCell>
            <TableCell>
              <ReleaseLink release={release} />
            </TableCell>
            <TableCell>{release.release_type.toUpperCase()}</TableCell>
            { release.review_count > 0 && (
              <TableCell>
                {release.avg_review}% ({release.review_count} reviews)
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

export const DiscographyCards = () => (
  <div>

  </div>
)

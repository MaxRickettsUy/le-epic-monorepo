import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Member } from "@/lib/types";

export const MemberTable = ({ members }: { members: Member[] }) => {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Role</TableHead>
          <TableHead>Other Bands</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {members.map((member, index) => (
          <TableRow key={`${member.name}-${index}`}>
            <TableCell className="font-medium">{member.name}</TableCell>
            <TableCell>{member.role ?? "—"}</TableCell>
            <TableCell>—</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

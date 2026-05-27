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
  if (members.length === 0) {
    return (
      <p className="p-4 text-sm text-muted-foreground">No members listed for this band yet.</p>
    );
  }

  return (
    <div className="max-h-[60vh] overflow-y-auto">
      <Table>
        <TableHeader className="sticky top-0 z-10 bg-background">
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Role</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {members.map((member, index) => (
            <TableRow key={`${member.name}-${index}`}>
              <TableCell className="font-medium">{member.name}</TableCell>
              <TableCell>{member.role ?? "—"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

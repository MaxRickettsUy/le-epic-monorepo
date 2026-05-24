"use client";

import { useParams } from "next/navigation";
import { ReleaseForm } from "@/components/forms/release-form";
import { createReleaseAction } from "@/app/actions";

export default function Page() {
  const params = useParams<{ bandId: string }>();
  const bandId = Number(params.bandId);

  if (!Number.isInteger(bandId) || bandId <= 0) {
    return <p className="p-[1rem]">Invalid band.</p>;
  }

  return (
    <ReleaseForm title="Add Release" onSubmit={(input) => createReleaseAction(bandId, input)} />
  );
}

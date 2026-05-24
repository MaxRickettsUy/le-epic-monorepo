"use client";

import { BandForm } from "@/components/forms/band-form";
import { createBandAction } from "@/app/actions";

export default function Page() {
  return <BandForm title="Add Band" onSubmit={(input) => createBandAction(input)} />;
}

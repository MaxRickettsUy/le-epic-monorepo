"use client";

import { BandForm } from "@/components/forms/band-form";
import { updateBandAction } from "@/app/actions";
import type { Band } from "@/lib/types";

export const EditBandForm = ({ band }: { band: Band }) => {
  return (
    <BandForm
      title="Edit Band"
      defaultValues={{
        name: band.name,
        status: band.status,
        location: band.location,
        country: band.country,
        label: band.label,
        band_picture: band.band_picture ?? null,
      }}
      onSubmit={(input) => updateBandAction(band.id, input)}
    />
  );
};

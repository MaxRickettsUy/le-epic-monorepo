"use client";

import { BandForm } from "@/components/forms/band-form";
import { updateBandAction } from "@/app/actions";
import type { Band } from "@/lib/types";
import { DeleteBandSection } from "./delete-band-section";

export const EditBandForm = ({ band }: { band: Band }) => {
  return (
    <>
      <BandForm
        title="Edit Band"
        defaultValues={{
          name: band.name,
          status: band.status,
          location: band.location,
          country: band.country,
          label: band.label,
          band_picture: band.band_picture ?? null,
          logo: band.logo ?? null,
          inclusion_reason: band.inclusion_reason ?? null,
        }}
        onSubmit={(input) => updateBandAction(band.id, input)}
      />
      <div className="flex flex-col gap-[1rem] p-[1rem]">
        <DeleteBandSection bandId={band.id} bandName={band.name} />
      </div>
    </>
  );
};

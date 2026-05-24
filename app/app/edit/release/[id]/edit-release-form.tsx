"use client";

import { ReleaseForm } from "@/components/forms/release-form";
import { updateReleaseAction } from "@/app/actions";
import type { ReleaseDetail } from "@/lib/types";

export const EditReleaseForm = ({ release }: { release: ReleaseDetail }) => {
  return (
    <ReleaseForm
      title="Edit Release"
      defaultValues={{
        name: release.name,
        label: release.label,
        release_type: release.release_type,
        year: release.year,
        length: release.length,
        art: release.art,
      }}
      onSubmit={(input) => updateReleaseAction(release.id, release.band_id, input)}
    />
  );
};

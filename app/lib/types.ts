// Types mirror the backend response contract in ../backend/app/schemas.py.

export type BandStatus = "active" | "unknown" | "on-hold" | "split-up";

export interface Member {
  name: string;
  role?: string | null;
}

export interface Track {
  id: number;
  name: string;
  length?: number | null;
  lyrics?: string | null;
  track_number?: number | null;
  position?: number | null;
  mbid?: string | null;
}

/** Release as nested under a band (no back-reference to the band). */
export interface Release {
  id: number;
  band_id: number;
  name: string;
  length?: number | null;
  art?: string | null;
  release_type?: string | null;
  /** Alias of `release_type` provided by the backend. */
  type?: string | null;
  label?: string | null;
  year?: number | null;
  release_group_mbid?: string | null;
  avg_review: number;
  review_count: number;
}

/** Band as nested under a release detail response. */
export interface BandSummary {
  id: number;
  name: string;
  location: string;
  country: string;
  label: string;
}

/** Release detail response (`GET /release/{id}`). */
export interface ReleaseDetail extends Release {
  band: BandSummary;
  tracks: Track[];
}

interface BandBase {
  id: number;
  name: string;
  status: BandStatus;
  band_picture?: string | null;
  location: string;
  country: string;
  label: string;
  mbid?: string | null;
}

/** Band as returned in the paginated list (`GET /band/`). */
export type BandListItem = BandBase;

/** Band detail response (`GET /band/{id}`). */
export interface Band extends BandBase {
  members: Member[];
  releases: Release[];
}

export interface BandList {
  bands: BandListItem[];
  next: number | null;
  prev: number | null;
}

export interface User {
  name: string;
}

export interface Review {
  author: User;
  release: Release;
  date: string;
}

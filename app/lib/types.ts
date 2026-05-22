export interface Member {
  name: string;
  role: string;
}

export interface Band {
  band_picture: string;
  id: number;
  name: string;
  country: string;
  location: string;
  members: Member[],
  releases: Release[]
  status: "active" | "unknown" | "on-hold" | "split-up";
  label: string;
}

// export interface Album {
//   name: string;
//   bandName: string;
//   year: number;
//   label: string;
//   rating: number;
//   reviewCount: number;
//   songs: Song[];
// }

export interface User {
  name: string;
}

export interface Review {
  author: User;
  release: Release;
  date: string;
}

export interface Song {
  name: string;
  length: string;
  lyrics?: string;
}

export interface Track {
  name: string;
  length: string;
  lyrics?: string;
}

export interface Release {
  art: string;
  band: Band;
  band_id: number;
  id: number;
  label?: string;
  length: number;
  name: string;
  release_type: string;
  avg_review: number;
  review_count: number;
  type: string;
  year: number;
}
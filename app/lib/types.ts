import { z } from "zod";

export interface Member {
  name: string;
  role: string;
}

export interface FlaskBand {
  band_picture: string;
  id: number;
  name: string;
  status: "active";
}

export interface Band {
  band_picture: string;
  id: number;
  name: string;
  members: Member[],
  releases: Release[]
  status: "active" | "unknown" | "inactive" | "split-up";
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
  id: number;
  name: string;
  band_id: string;
  band_name: string;
  band_picture: string;
  review_avg: number;
  review_count: number;
  status: "active" | "split-up" | "unknown" | 'inactive';
  tracks: Track[];
  year: number;
}
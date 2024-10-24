import { z } from "zod";

export interface Member {
  name: string;
  role: string;
}

export interface Band {
  name: string;
  status: "active" | "unknown" | "rip";
  members: Member[],
  discography: Album[]
}

export interface Album {
  name: string;
  bandName: string;
  year: number;
  label: string;
  rating: number;
  reviewCount: number;
  songs: Song[];
}

export interface User {
  name: string;
}

export interface Review {
  author: User;
  album: Album;
  date: string;
}

export interface Song {
  name: string;
  length: string;
  lyrics?: string;
}
import { z } from "zod";

export interface Artist {
  name: string;
  status: "active" | "unknown" | "rip";
}

export interface Album {
  name: string;
  // artist: Artist | Artist[];
  artist: Artist;
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
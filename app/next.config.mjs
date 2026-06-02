/** @type {import('next').NextConfig} */
const nextConfig = {
  // ...
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "loremflickr.com",
        port: "",
        pathname: "/640/**",
      },
      // Album art (Cover Art Archive) — `seed.cover_art` writes URLs here.
      { protocol: "https", hostname: "coverartarchive.org" },
      // Band art (Wikidata → Wikimedia Commons) — `seed.band_art` writes
      // Special:FilePath URLs that 302 to upload.wikimedia.org.
      { protocol: "https", hostname: "commons.wikimedia.org" },
      { protocol: "https", hostname: "upload.wikimedia.org" },
      // Escape hatch for a future CDN; opt-in via env.
      ...(process.env.NEXT_PUBLIC_ART_HOST
        ? [{ protocol: "https", hostname: process.env.NEXT_PUBLIC_ART_HOST }]
        : []),
    ],
  },
  // ...
};

export default nextConfig;

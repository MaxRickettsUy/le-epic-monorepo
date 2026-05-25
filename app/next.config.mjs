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
      // Band/release art hosts are not yet finalized (see plan open question #3).
      // Allow an explicit host via env until the CDN is decided, instead of a
      // wildcard that would permit any https origin.
      ...(process.env.NEXT_PUBLIC_ART_HOST
        ? [{ protocol: "https", hostname: process.env.NEXT_PUBLIC_ART_HOST }]
        : []),
    ],
  },
  // ...
};

export default nextConfig;

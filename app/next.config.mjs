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
      // Until then, allow any https host so backend-provided URLs render. Tighten
      // to specific hosts once the art CDN is decided.
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
  // ...
};

export default nextConfig;

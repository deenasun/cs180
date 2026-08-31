import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: {
    unoptimized: true, // Disable image optimization for static export
  },
  // GitHub Pages serves this project from /cs180
  // `npm run build && npm run serve` serves the contents of out/ from the root URL.
  basePath: process.env.GITHUB_ACTIONS === "true" ? "/cs180" : "",
  trailingSlash: true,
};

export default nextConfig;

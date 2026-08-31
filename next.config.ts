import type { NextConfig } from "next";

const basePath = process.env.GITHUB_ACTIONS === "true" ? "/cs180" : "";

const nextConfig: NextConfig = {
  output: "export",
  // GitHub Pages serves this project from /cs180
  // `npm run build && npm run serve` serves the contents of out/ from the root URL.
  basePath,
  env: {
    NEXT_PUBLIC_BASE_PATH: basePath,
  },
  images: {
    unoptimized: true, // Disable image optimization for static export
  },
  trailingSlash: true,
};

export default nextConfig;

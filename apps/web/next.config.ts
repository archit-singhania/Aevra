import path from "node:path";
import type { NextConfig } from "next";

const apiOrigin =
  process.env.AEVRA_API_ORIGIN ??
  (process.env.AEVRA_STANDALONE === "1" ? "http://api:8000" : "http://localhost:8000");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: process.env.AEVRA_STANDALONE === "1" ? "standalone" : undefined,
  // Keep tracing inside this monorepo when a parent workspace also contains a lockfile.
  outputFileTracingRoot: path.join(process.cwd(), ".."),
  poweredByHeader: false,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

import path from "node:path";
import type { NextConfig } from "next";

const isVercel = process.env.VERCEL === "1" || process.env.VERCEL === "true";
const useStandalone = process.env.AEVRA_STANDALONE === "1" && !isVercel;
const apiOrigin =
  process.env.AEVRA_API_ORIGIN ?? (useStandalone ? "http://api:8000" : "http://localhost:8000");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Docker needs a self-contained server; Vercel must use its native Next runtime.
  output: useStandalone ? "standalone" : undefined,
  // Keep tracing inside this monorepo when a parent workspace also contains a lockfile.
  outputFileTracingRoot: path.resolve(__dirname, "../.."),
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

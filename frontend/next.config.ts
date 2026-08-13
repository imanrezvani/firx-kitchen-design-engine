import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Reverse proxy: /api/* is forwarded to the FastAPI backend so the
  // preview (single exposed port) can serve frontend + backend together.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
  // Allow access from the monkeycode-ai.live preview domains.
  allowedDevOrigins: ["*.monkeycode-ai.live"],
};

export default nextConfig;

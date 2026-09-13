import type { NextConfig } from "next";

const configuredApiUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL;
const backendOrigin = (configuredApiUrl || "http://127.0.0.1:8000")
  .replace(/\/api\/v1\/?$/, "")
  .replace(/\/$/, "");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendOrigin}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;

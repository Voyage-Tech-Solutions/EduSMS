import type { NextConfig } from "next";

const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://edusms-ke1l.onrender.com';

const nextConfig: NextConfig = {
  reactCompiler: true,
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  images: {
    domains: ['bdaiectbtlwpdkprocef.supabase.co'],
    formats: ['image/avif', 'image/webp'],
  },
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${API_URL}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;

import type { NextConfig } from "next";

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
};

export default nextConfig;

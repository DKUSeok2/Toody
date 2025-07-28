import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Socket.io 404 오류 방지
  async rewrites() {
    return [
      {
        source: '/socket.io/:path*',
        destination: '/404', // 404 페이지로 리다이렉트
      },
    ];
  },
};

export default nextConfig;

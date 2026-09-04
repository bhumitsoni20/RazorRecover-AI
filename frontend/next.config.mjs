/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: process.env.BUILD_STANDALONE ? "standalone" : undefined,
};

export default nextConfig;

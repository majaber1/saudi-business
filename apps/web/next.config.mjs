/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The FastAPI backend base URL is provided via NEXT_PUBLIC_API_BASE_URL.
  // Left unset in demo/preview builds; the UI degrades gracefully.
};

export default nextConfig;

import { fileURLToPath } from 'url'
import { dirname } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

/** @type {import('next').NextConfig} */
const nextConfig = {
  devIndicators: false,

  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  
  // Set turbopack root to current directory to avoid lockfile detection warnings
  experimental: {
    turbo: {
      root: process.cwd(),
    },
  },
}

export default nextConfig

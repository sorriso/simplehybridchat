// path: frontend/next.config.js
// version: 3
//
// Changes in v3:
// - FIXED: Changed output from 'export' to 'standalone' for Docker deployment
// - REMOVED: trailingSlash option (not needed for standalone)
// - Reason: Static export doesn't support dynamic features, standalone is better for Docker

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,
  
  // Use standalone output for Docker deployment
  output: 'standalone',
  
  // Disable image optimization for better performance with external images
  images: {
    unoptimized: true,
  },
  
  // Environment variables exposed to browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig
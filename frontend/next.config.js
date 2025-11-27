// path: ./next.config.js
// version: 1

/** @type {import('next').NextConfig} */
const nextConfig = {
    // Enable React strict mode for better development experience
    reactStrictMode: true,
    
    // Enable static export for serving with Caddy
    output: 'export',
    
    // Disable image optimization for static export
    images: {
      unoptimized: true,
    },
    
    // Optional: Add trailing slash for better static serving
    trailingSlash: true,
  }
  
  module.exports = nextConfig
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Disable source maps in development to avoid map issues
  productionBrowserSourceMaps: false,
  // Ensure proper CSS processing
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      config.devtool = 'cheap-module-source-map'
    }
    return config
  },
}

module.exports = nextConfig

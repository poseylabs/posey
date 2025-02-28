import type { NextConfig } from "next";

const allowedPorts = [2222, 5173, 5555, 8888, 9999]
const allowedOrigins = allowedPorts.map(port => `http://localhost:${port}`)

const securityHeaders = [
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block'
  },
  {
    key: 'X-Frame-Options',
    value: 'SAMEORIGIN'
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff'
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=31536000; includeSubDomains'
  }
];

const nextConfig: NextConfig = {
  devIndicators: {
    appIsrStatus: false,
    buildActivity: process.env.NODE_ENV === 'development' ? true : false,
    buildActivityPosition: 'top-right'
  },
  transpilePackages: ["@posey.ai/ui", "@posey.ai/core", "@posey.ai/state"],
  experimental: {
    serverActions: {
      bodySizeLimit: '20mb',
    },
  },
  async headers() {
    return [
      {
        // Allow CORS for the UI dev server
        source: '/(.*)',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            // Allow both the UI dev server and the desktop app
            value: process.env.NODE_ENV === 'development' ? '*' : allowedOrigins.join(', ')
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, OPTIONS, POST, PUT, DELETE',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'X-Requested-With, Authorization, Content-Type',
          },
          {
            // Add this to handle preflight requests
            key: 'Access-Control-Allow-Credentials',
            value: 'true',
          },
          ...securityHeaders
        ],
      },
    ];
  },
  webpack: (config, { isServer }) => {
    config.module.exprContextCritical = false;

    config.resolve.alias = {
      ...config.resolve.alias,
    };

    if (!isServer) {
      config.watchOptions = {
        ignored: ['**/.git/**', '**/node_modules/**']
      }
    }

    return config;
  }
};

export default nextConfig;

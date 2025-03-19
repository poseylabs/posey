import type { NextConfig } from "next";

const allowedPorts = [2222, 3000, 3333, 5173, 5555, 8000, 8888, 9999]
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

    // Handle WebAssembly files for PDF.js
    config.experiments = {
      ...config.experiments,
      asyncWebAssembly: true,
    };

    // Add fallbacks for PDF.js dependencies
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        canvas: false,
        encoding: false,
        'pdfjs-dist/build/pdf.worker': false,
        'qcms_bg.wasm': false,
      };
    }

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

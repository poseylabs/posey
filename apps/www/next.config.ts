/// <reference types="node" />

import type { NextConfig } from "next";
import pnp from "pnpapi";

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
    externalDir: true,
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
  webpack: (config, { isServer, defaultLoaders }) => {
    config.module.exprContextCritical = false;

    config.resolve.alias = {
      ...config.resolve.alias,
    };

    // Add custom externals function for PnP compatibility
    // config.externals = [
    //   // @ts-ignore:next-line
    //   (ctx, callback) => {
    //     // Check if the request is a bare specifier (package name)
    //     if (ctx.request && /^[^./\\]/.test(ctx.request)) {
    //       try {
    //         const resolvedPath = pnp.resolveToUnqualified(ctx.request, ctx.context, {
    //           considerBuiltins: false,
    //         });
    //         // Externalize using the resolved path
    //         return callback(null, "commonjs " + resolvedPath);
    //       } catch (error) {
    //         // If pnpapi can't resolve it, let Webpack handle it normally
    //         // console.warn(`PNP Resolve Failed for ${ctx.request}:`, error);
    //       }
    //     }
    //     // Continue without externalizing
    //     // @ts-ignore:next-line
    //     callback();
    //   },
    //   ...(Array.isArray(config.externals) ? config.externals : [config.externals].filter(Boolean)),
    // ];

    if (!isServer) {
      config.watchOptions = {
        ignored: ['**/.git/**', '**/node_modules/**']
      }
    }

    return config;
  },
};

export default nextConfig;

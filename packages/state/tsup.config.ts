import dotenv from 'dotenv';
import { defineConfig } from "tsup";

dotenv.config();

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm"],
  dts: false,
  sourcemap: true,
  clean: true,
  treeshake: true,
  splitting: false,
  target: 'es2020',
  platform: 'browser',
  external: [
    'react',
    'react-dom',
    'react/jsx-runtime',  
    'crypto',
    'fs',
    'path',
    'os',
    'stream',
    'http',
    'https',
    'url',
    'util',
    'zlib',
    'node:crypto',
    'node:fs',
    'node:stream',
    'node:stream/web'
  ],

  esbuildOptions(options) {
    options.bundle = true
    options.define = {
      ...options.define,
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
      'process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT': JSON.stringify(process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT),
    }
    options.platform = 'browser'
    options.conditions = ['import', 'module']
    options.alias = {
      '@/*': './src/*'
    }
    options.external = [
      ...options.external || [],
      'node:crypto',
      'node:fs',
      'node:stream',
      'node:stream/web',
      'react/jsx-runtime'
    ]
    options.logOverride = {
      'equals-negative-zero': 'silent',
      'unsupported-dynamic-import': 'silent',
      'mixed-exports': 'silent'
    }
    options.mainFields = ['module', 'main']
    options.jsx = 'automatic'
    options.format = 'esm'
  },
  minify: true,
  outExtension({ format }) {
    return {
      js: format === 'cjs' ? '.cjs' : '.mjs',
    }
  }
}); 

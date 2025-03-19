import { defineConfig } from 'tsup'

export default defineConfig({
  entry: {
    'index': 'src/index.ts',
    'database/index': 'src/database/index.ts',
    'config/index': 'src/config/index.ts',
    'prompts/index': 'src/prompts/index.ts',
    'types/index': 'src/types/index.ts',
    'utils/index': 'src/utils/index.ts',
    'helpers/index': 'src/helpers/index.ts',
  },
  format: ['esm'],
  dts: true,
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
    'bson',
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
    'node:stream/web',
    'dns',
    'net',
    'timers',
    'child_process',
    'tls',
    'timers/promises',
    'node:events',
    'node:process',
    'node:util',
    'assert',
    'tty'
  ],
  esbuildOptions(options) {
    options.bundle = true
    options.platform = 'browser'
    options.conditions = ['import', 'module']
    options.alias = {
      crypto: 'crypto-browserify',
      fs: 'browserify-fs',
      path: 'browserify-path',
    }
    options.external = [
      ...options.external || [],
      'node:crypto',
      'node:fs',
      'node:stream',
      'node:stream/web',
      'react/jsx-runtime',
      'dns',
      'net',
      'timers',
      'child_process',
      'tls',
      'timers/promises',
      'node:events',
      'node:process',
      'node:util',
      'assert',
      'tty'
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
  minify: false,
  outExtension({ format }) {
    return {
      js: format === 'cjs' ? '.cjs' : '.mjs',
    }
  },
  outDir: 'dist'
}) 

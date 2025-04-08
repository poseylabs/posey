import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'
import dts from 'vite-plugin-dts'
import { resolve } from 'path'
import dotenv from 'dotenv'

dotenv.config()

const defaultConfig: any = () => {

  return {
    plugins: [
      react(),
      tsconfigPaths(),
      dts({
        insertTypesEntry: true,
      }),
      // libInjectCss(),
    ],
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: '@use "sass:math";',
        },
      },
      modules: {
        generateScopedName: '[name]__[local]___[hash:base64:5]',
      },
    },
    build: {
      // cssCodeSplit: false,
      lib: {
        entry: {
          index: resolve(__dirname, 'src/index.ts'),
          'components/index': resolve(__dirname, 'src/components/index.ts'),
          'components/chat/index': resolve(__dirname, 'src/components/chat/index.ts'),
          'components/form/index': resolve(__dirname, 'src/components/form/index.ts'),
          'components/auth/index': resolve(__dirname, 'src/components/auth/index.ts'),
          'components/layout/index': resolve(__dirname, 'src/components/layout/index.ts'),
          'components/navigation/index': resolve(__dirname, 'src/components/navigation/index.ts'),
          'components/posey/index': resolve(__dirname, 'src/components/posey/index.ts'),
          'components/preferences/index': resolve(__dirname, 'src/components/preferences/index.ts'),
          'components/status/index': resolve(__dirname, 'src/components/status/index.ts'),
          'components/user/index': resolve(__dirname, 'src/components/user/index.ts'),
          'config/index': resolve(__dirname, 'src/config/index.ts'),
          'style/index': resolve(__dirname, 'src/style/index.ts'),
          'types/index': resolve(__dirname, 'src/types/index.ts'),
        },
        formats: ['es'],
        fileName: (format, entryName) => `${entryName}.mjs`,
        cssFileName: 'style/posey.ui.css',
        // cssCodeSplit: false,
      },
      rollupOptions: {
        external: [
          'react',
          'react-dom',
          '@heroui/react',
          'tailwindcss',
          'fs',
          'path',
          'crypto',
          'stream',
          'http',
          'https',
          'zlib',
          'os',
          'axios',
          'openai',
          'elevenlabs',
          'lodash/debounce',
          'next/link',
          'next/navigation',
          'react-router-dom',
          'zustand',
          'ollama',
          'node:fs',
          'node:path',
          '__vite-browser-external'
        ],
        output: {
          assetFileNames: '[name][extname]',
          globals: {
            react: 'React',
            'react-dom': 'ReactDOM',
            'ollama': 'Ollama'
          }
        },
      },
      commonjsOptions: {
        transformMixedEsModules: true,
        exclude: [/node_modules\/core-js/],
      },
      copyPublicDir: false,
      watch: process.env.WATCH === 'true' ? {} : null,
      sourcemap: true,
      resolve: {
        alias: {
          'node:fs': 'rollup-plugin-node-polyfills/polyfills/fs',
          'node:path': 'rollup-plugin-node-polyfills/polyfills/path'
        }
      }
    },
    server: {
      port: process.env.PORT ? parseInt(process.env.PORT) : 5173,
      open: false,
    },
    exports: 'named',
    define: {
      'process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT':
        JSON.stringify(process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT),
      'process.env.POSTGRES_USER':
        JSON.stringify(process.env.POSTGRES_USER),
      'process.env.POSTGRES_PASSWORD':
        JSON.stringify(process.env.POSTGRES_PASSWORD),
      'process.env.POSTGRES_HOST':
        JSON.stringify(process.env.POSTGRES_HOST),
      'process.env.POSTGRES_PORT':
        JSON.stringify(process.env.POSTGRES_PORT),
      'process.env.POSTGRES_DATABASE':
        JSON.stringify(process.env.POSTGRES_DATABASE),
      'process.env.NEXT_PUBLIC_API_ENDPOINT':
        JSON.stringify(process.env.NEXT_PUBLIC_API_ENDPOINT),
    },
    watch: {
      include: ['src/**'],
      exclude: ['node_modules/**', 'dist/**']
    },
  }
}

export default defineConfig(defaultConfig)

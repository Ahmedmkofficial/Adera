import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendTarget = env.BACKEND_URL || env.VITE_BACKEND_URL || 'http://backend:8000'

  const apiPrefixes = [
    '/auth',
    '/risk',
    '/reports',
    '/transactions',
    '/recipients',
    '/alerts',
    '/cases',
    '/dashboard',
    '/admin/reports',
    '/health',
    '/docs',
    '/openapi.json',
    '/redoc',
  ]

  const proxy = {}
  for (const prefix of apiPrefixes) {
    proxy[prefix] = {
      target: backendTarget,
      changeOrigin: true,
    }
  }

  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy,
    },
    test: {
      environment: 'jsdom',
      setupFiles: './src/test/setup.js',
      css: false,
      testTimeout: 15000,
      fileParallelism: false,
    },
  }
})

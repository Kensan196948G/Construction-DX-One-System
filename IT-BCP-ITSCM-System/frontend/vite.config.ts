import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': resolve(__dirname, 'src') },
  },
  server: {
    port: 3004,
    proxy: {
      '/api': { target: 'http://localhost:8004', changeOrigin: true },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      include: ['src/stores/**', 'src/api/**'],
      exclude: ['src/api/client.ts'],
      thresholds: { lines: 60 },
    },
  },
})

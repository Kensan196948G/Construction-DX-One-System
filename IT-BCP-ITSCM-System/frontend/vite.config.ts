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
    exclude: ['**/node_modules/**', '**/e2e/**', '**/*.spec.ts'],
    coverage: {
      provider: 'v8',
      include: ['src/stores/**', 'src/api/**'],
      thresholds: { lines: 60 },
    },
  },
})

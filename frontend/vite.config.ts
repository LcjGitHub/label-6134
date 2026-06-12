import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 6101,
    strictPort: false,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:6000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 6101,
    strictPort: false,
    host: true,
  },
})

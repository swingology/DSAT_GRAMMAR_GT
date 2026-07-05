import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    allowedHosts: ['jb-2410.tail0cecc1.ts.net', '.ts.net'],
    port: 5174,
    proxy: {
      // Backend mounts admin/users routers WITHOUT the /api prefix (bug-777/778);
      // strip it here so the client's uniform /api base works in dev.
      '/api/admin': {
        target: process.env.VITE_BACKEND_ORIGIN || 'http://localhost:8000',
        rewrite: (p: string) => p.replace(/^\/api/, ''),
      },
      '/api/users': {
        target: process.env.VITE_BACKEND_ORIGIN || 'http://localhost:8000',
        rewrite: (p: string) => p.replace(/^\/api/, ''),
      },
      '/api': process.env.VITE_BACKEND_ORIGIN || 'http://localhost:8000',
    },
  },
})

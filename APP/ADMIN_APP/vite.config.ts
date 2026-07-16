import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  // Load .env so VITE_BACKEND_ORIGIN governs the dev proxy. Vite only feeds .env
  // into import.meta.env for the client bundle — it does NOT populate process.env
  // for the config itself, so a bare `process.env.VITE_BACKEND_ORIGIN` read here
  // silently defaults to :8000 and 502s in the dev stack (backend is on :8002).
  // Fall back to a real process-env export for shells that set it explicitly.
  const env = loadEnv(mode, process.cwd(), '')
  const backendOrigin =
    env.VITE_BACKEND_ORIGIN || process.env.VITE_BACKEND_ORIGIN || 'http://localhost:8000'

  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: '0.0.0.0',
      allowedHosts: ['jb-2410.tail0cecc1.ts.net', '.ts.net'],
      port: 5174,
      proxy: {
        // Backend mounts admin/users routers WITHOUT the /api prefix (bug-777/778);
        // strip it here so the client's uniform /api base works in dev.
        '/api/admin': {
          target: backendOrigin,
          rewrite: (p: string) => p.replace(/^\/api/, ''),
        },
        '/api/users': {
          target: backendOrigin,
          rewrite: (p: string) => p.replace(/^\/api/, ''),
        },
        '/api': backendOrigin,
      },
    },
  }
})

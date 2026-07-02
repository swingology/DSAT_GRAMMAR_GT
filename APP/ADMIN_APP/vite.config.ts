import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5175,
    proxy: {
      // student.router (stats/study) mounts at /api; users.router at /users;
      // admin.router at /admin — client.ts calls each with its real prefix.
      '/api': 'http://localhost:8002',
      '/users': 'http://localhost:8002',
      '/admin': 'http://localhost:8002',
    },
  },
})

import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['src/vitest.setup.ts'],
    // Dep (re-)optimization segfaults the default worker-thread pool on Linux — any
    // cold cache (e.g. a newly added source directory) takes the whole run down.
    // Forks are immune. Same class of issue as the esbuild pin in vite.config.ts.
    pool: 'forks',
    env: {
      VITE_TEST_USER_TOKEN: 'test-token-vitest',
    },
  },
})

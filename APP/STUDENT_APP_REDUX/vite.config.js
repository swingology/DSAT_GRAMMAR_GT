import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
function resolveBackendTarget(mode) {
    const env = loadEnv(mode, process.cwd(), '');
    const candidate = env.BACKEND_PROXY_URL ?? env.VITE_API_BASE;
    if (candidate?.startsWith('http://') || candidate?.startsWith('https://')) {
        return candidate;
    }
    return 'http://127.0.0.1:8000';
}
export default defineConfig(({ mode }) => ({
    plugins: [react()],
    optimizeDeps: {
        // Vite 8 uses Rolldown for dep pre-bundling; fall back to esbuild which
        // handles react-dom's CJS dev bundle without parse errors.
        bundler: 'esbuild',
    },
    server: {
        host: '0.0.0.0',
        port: 5173,
        allowedHosts: ['jb-2410.tail0cecc1.ts.net', '.ts.net'],
        proxy: {
            '/api': {
                target: resolveBackendTarget(mode),
                changeOrigin: true,
            }
        }
    }
}));

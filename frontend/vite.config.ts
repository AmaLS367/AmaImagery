import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_API_TARGET || 'http://localhost:8000'

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      cors: { origin: '*' },
      hmr: { protocol: 'wss', clientPort: 443 },
      proxy: {
        '/generate': { target, changeOrigin: true, secure: false },
        '/health':   { target, changeOrigin: true, secure: false },
        '/file':     { target, changeOrigin: true, secure: false },
      },
    },
  }
})

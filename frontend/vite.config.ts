import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_API_TARGET || env.VITE_API_URL || 'http://localhost:8000'

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': '/src'
      }
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      cors: { origin: '*' },
      hmr: { protocol: 'ws' },
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  }
})

// (Universal configuration for *.trycloudflare.com and other tunnels):
// server: {
//   host: true,
//   allowedHosts: true, // Disables host verification
//   hmr: {
//     protocol: 'https',
//     clientPort: 443,
//   },
// }


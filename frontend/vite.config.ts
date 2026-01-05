import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_API_TARGET || 'http://localhost:8000'

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
        '/generate': { 
          target, 
          changeOrigin: true, 
          secure: false,
          configure: (proxy, options) => {
            proxy.on('error', (err, req, res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (proxyReq, req, res) => {
              console.log('Sending Request:', req.method, req.url);
            });
            proxy.on('proxyRes', (proxyRes, req, res) => {
              console.log('Received Response:', proxyRes.statusCode);
            });
          }
        },
        '/health':   { target, changeOrigin: true, secure: false },
        '/file':     { target, changeOrigin: true, secure: false },
        '/auth':     { target, changeOrigin: true },
        '/users':    { target, changeOrigin: true },
      },
    },
  }
})

// (универсально для любых *.trycloudflare.com и прочих туннелей):

// server: {
//   host: true,
//   allowedHosts: true, // отключает проверку хоста
//   hmr: {
//     protocol: 'https',
//     clientPort: 443,
//   },
// }
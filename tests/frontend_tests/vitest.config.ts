import { defineConfig } from 'vitest/config'
import path from 'path'
export default defineConfig({
  test: {
    include: ['unit/**/*.test.ts', 'unit/**/*.test.tsx'],
    environment: 'jsdom',
    setupFiles: [path.resolve(__dirname, './setup.ts')],
  },
  resolve: {
    dedupe: ['react', 'react-dom'],
    alias: {
      '@src': path.resolve(__dirname, '../../frontend/src'),
      react: path.resolve(__dirname, '../../frontend/node_modules/react'),
      'react-dom': path.resolve(__dirname, '../../frontend/node_modules/react-dom'),
      'react/jsx-runtime': path.resolve(__dirname, '../../frontend/node_modules/react/jsx-runtime.js'),
      'react/jsx-dev-runtime': path.resolve(__dirname, '../../frontend/node_modules/react/jsx-dev-runtime.js'),
      '@testing-library/react': path.resolve(__dirname, '../../frontend/node_modules/@testing-library/react'),
      '@testing-library/jest-dom/vitest': path.resolve(
        __dirname,
        '../../frontend/node_modules/@testing-library/jest-dom/vitest.js',
      ),
    },
  },
})

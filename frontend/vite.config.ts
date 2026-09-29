import { defineConfig } from 'vitest/config';

export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: { target: 'es2022' },
  test: { environment: 'jsdom', setupFiles: './tests/setup.ts', include: ['tests/unit/**/*.test.ts'] },
});

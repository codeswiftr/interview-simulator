import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/polyfills.ts', './src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: ['node_modules/', 'src/test/', '**/*.d.ts'],
    },
    env: {
      VITE_API_URL: 'http://localhost:8000/api/v1',
    },
    environmentOptions: {
      jsdom: {
        url: 'http://localhost:3000/',
        resources: 'usable',
      },
    },
    // Disable threads to avoid memory issues
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: true,
      },
    },
    // Force MSW and is-node-process to be processed after jsdom environment is ready
    server: {
      deps: {
        inline: ['msw', 'is-node-process'],
      },
    },
    deps: {
      optimizer: {
        web: {
          include: ['msw', 'is-node-process'],
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});

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
    environmentOptions: {
      jsdom: {
        url: 'http://localhost:3000/',
        resources: 'usable',
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

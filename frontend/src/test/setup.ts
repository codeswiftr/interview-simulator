// Polyfills are loaded first via vitest.config.ts setupFiles
import '@testing-library/jest-dom';
import * as matchers from 'vitest-axe/matchers';
import { expect, afterEach, beforeEach, afterAll, beforeAll, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

expect.extend(matchers);

// Mock PostHog globally to prevent initialization issues
vi.mock('posthog-js', () => ({
  default: {
    init: vi.fn(),
    identify: vi.fn(),
    capture: vi.fn(),
    reset: vi.fn(),
    has_opted_out_capturing: vi.fn(() => false),
    opt_out_capturing: vi.fn(),
    opt_in_capturing: vi.fn(),
  },
}));

// MSW server - dynamically imported to ensure polyfills run first
let server: Awaited<typeof import('./mocks/server')>['server'];

// Start MSW server before all tests
beforeAll(async () => {
  // Dynamic import ensures localStorage polyfill is ready
  const msw = await import('./mocks/server');
  server = msw.server;
  server.listen({ onUnhandledRequest: 'warn' });
});

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  // Reset handlers to default after each test
  server?.resetHandlers();
});

// Stop MSW server after all tests
afterAll(() => {
  server?.close();
});

// Mock window.matchMedia for ThemeContext
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => true,
  }),
});

// Mock Element.scrollIntoView for components that use it
Element.prototype.scrollIntoView = () => {};

// Mock localStorage BEFORE importing anything else
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Now import everything else
import '@testing-library/jest-dom';
import * as matchers from 'vitest-axe/matchers';
import { expect } from 'vitest';
import { cleanup } from '@testing-library/react';

expect.extend(matchers);
import { afterEach, beforeEach } from 'vitest';

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
});

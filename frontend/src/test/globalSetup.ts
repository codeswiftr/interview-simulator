// Global setup runs BEFORE vitest processes any test files
// This sets up the environment for MSW which needs localStorage at import time

export function setup() {
  // This runs in the main vitest process, not in test workers
  // For localStorage polyfill, we need to use env options instead
}

export function teardown() {
  // Cleanup
}

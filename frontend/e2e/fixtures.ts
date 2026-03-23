import { test as base } from '@playwright/test';

/**
 * Test fixtures for E2E tests
 */

export interface TestUser {
  email: string;
  password: string;
  token?: string;
}

export const test = base.extend<{
  testUser: TestUser;
}>({
  testUser: async ({ page: _page }, use) => {
    // Generate unique test user
    const timestamp = Date.now();
    const testUser: TestUser = {
      email: `test-${timestamp}@example.com`,
      password: 'TestPassword123!',
    };

    await use(testUser);
  },
});

export { expect } from '@playwright/test';

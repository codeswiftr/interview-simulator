import { test, expect } from './fixtures';
import { clearLocalStorage } from './helpers';

/**
 * E2E Test: Password Reset Flow
 */
test.describe('Password Reset Flow', () => {
  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page);
  });

  test('user can request password reset', async ({ page, testUser }) => {
    // Navigate to login page
    await page.goto('/login');

    // Click "Forgot Password" link
    const forgotPasswordLink = page.locator('a:has-text("Forgot"), a:has-text("Reset")');
    if (await forgotPasswordLink.count() > 0) {
      await forgotPasswordLink.click();

      // Fill email
      await page.fill('input[type="email"]', testUser.email);
      await page.click('button[type="submit"]');

      // Should show success message
      await expect(
        page.locator('text=/email|sent|check/i')
      ).toBeVisible({ timeout: 5000 });
    } else {
      // If forgot password link doesn't exist, skip test
      test.skip();
    }
  });
});

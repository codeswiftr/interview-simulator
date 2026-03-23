import { test, expect } from './fixtures';
import { clearLocalStorage } from './helpers';

/**
 * E2E Test: Register → Dashboard
 * 
 * Tests the complete user registration flow and dashboard access.
 */
test.describe('Register → Dashboard Flow', () => {
  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page);
  });

  test('user can register and access dashboard', async ({ page, testUser }) => {
    // Navigate to register page
    await page.goto('/register');
    await expect(page).toHaveTitle(/CareerSwiftr|Interview Simulator/i);

    // Fill registration form
    await page.fill('input[type="email"]', testUser.email);
    await page.fill('input[type="password"]', testUser.password);
    await page.fill('input[name="confirmPassword"]', testUser.password);

    // Select experience level if present
    const experienceSelect = page.locator('select[name="experience_level"]');
    if (await experienceSelect.count() > 0) {
      await experienceSelect.selectOption('mid');
    }

    // Submit registration
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await page.waitForURL('/dashboard', { timeout: 10000 });

    // Verify dashboard elements
    await expect(page.locator('h1, h2')).toContainText(/dashboard|interviews/i);
    
    // Verify user is logged in (check for logout button or user menu)
    const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout")');
    await expect(logoutButton).toBeVisible({ timeout: 5000 });
  });

  test('registration with invalid email shows error', async ({ page, testUser }) => {
    await page.goto('/register');
    
    await page.fill('input[type="email"]', 'invalid-email');
    await page.fill('input[type="password"]', testUser.password);
    await page.fill('input[name="confirmPassword"]', testUser.password);
    
    await page.click('button[type="submit"]');

    // Should show validation error
    await expect(page.locator('text=/email|invalid/i')).toBeVisible({ timeout: 3000 });
  });

  test('registration with mismatched passwords shows error', async ({ page, testUser }) => {
    await page.goto('/register');
    
    await page.fill('input[type="email"]', testUser.email);
    await page.fill('input[type="password"]', testUser.password);
    await page.fill('input[name="confirmPassword"]', 'DifferentPassword123!');
    
    await page.click('button[type="submit"]');

    // Should show password mismatch error
    await expect(page.locator('text=/password|match/i')).toBeVisible({ timeout: 3000 });
  });
});

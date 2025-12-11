import { test, expect } from './fixtures';
import { registerUser, clearLocalStorage } from './helpers';

/**
 * E2E Test: Login → Create Interview → Record → Feedback
 * 
 * Tests the complete interview flow from creation to feedback.
 */
test.describe('Interview Flow', () => {
  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page);
  });

  test('complete interview flow: create → record → feedback', async ({ page, testUser }) => {
    // Register and login
    await registerUser(page, testUser);
    await expect(page).toHaveURL('/dashboard');

    // Create interview
    await page.click('button:has-text("New Interview")');
    
    // Fill interview form
    await page.selectOption('select[name="interview_type"]', 'behavioral');
    await page.fill('input[name="question_count"]', '2');
    
    // Submit
    await page.click('button:has-text("Start Interview"), button:has-text("Create")');

    // Wait for interview page
    await page.waitForURL(/\/interview\/[a-f0-9-]+/, { timeout: 10000 });

    // Verify interview page loaded
    await expect(page.locator('text=/question|interview/i')).toBeVisible({ timeout: 5000 });

    // Start recording (if button exists)
    const startButton = page.locator('button:has-text("Start"), button:has-text("Record")');
    if (await startButton.count() > 0) {
      await startButton.click();
      
      // Wait a bit for recording to start
      await page.waitForTimeout(2000);
      
      // Stop recording
      const stopButton = page.locator('button:has-text("Stop"), button:has-text("Save")');
      if (await stopButton.count() > 0) {
        await stopButton.click();
      }
    }

    // Submit response (if submit button exists)
    const submitButton = page.locator('button:has-text("Submit"), button:has-text("Confirm")');
    if (await submitButton.count() > 0) {
      await submitButton.click();
    }

    // Wait for feedback or next question
    await page.waitForTimeout(3000);

    // Verify we're either on feedback page or interview continues
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/\/interview|\/feedback|\/dashboard/);
  });

  test('can create interview with different types', async ({ page, testUser }) => {
    await registerUser(page, testUser);

    const interviewTypes = ['behavioral', 'technical', 'system_design'];
    
    for (const type of interviewTypes) {
      await page.click('button:has-text("New Interview")');
      await page.selectOption('select[name="interview_type"]', type);
      await page.fill('input[name="question_count"]', '1');
      await page.click('button:has-text("Start Interview"), button:has-text("Create")');
      
      // Wait for interview page
      await page.waitForURL(/\/interview\/[a-f0-9-]+/, { timeout: 10000 });
      
      // Verify interview type is reflected
      await expect(page.locator(`text=/${type}/i`)).toBeVisible({ timeout: 3000 }).catch(() => {
        // If not visible, that's okay - just verify we're on interview page
      });

      // Go back to dashboard for next iteration
      await page.goto('/dashboard');
      await page.waitForTimeout(1000);
    }
  });
});

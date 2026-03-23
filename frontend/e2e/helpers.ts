import { Page } from '@playwright/test';
import type { TestUser } from './fixtures';

/**
 * Helper functions for E2E tests
 */

export async function registerUser(page: Page, user: TestUser): Promise<void> {
  await page.goto('/register');
  await page.fill('input[type="email"]', user.email);
  await page.fill('input[type="password"]', user.password);
  await page.fill('input[name="confirmPassword"]', user.password);
  await page.click('button[type="submit"]');
  // Wait for redirect to dashboard
  await page.waitForURL('/dashboard', { timeout: 5000 });
}

export async function loginUser(page: Page, user: TestUser): Promise<void> {
  await page.goto('/login');
  await page.fill('input[type="email"]', user.email);
  await page.fill('input[type="password"]', user.password);
  await page.click('button[type="submit"]');
  // Wait for redirect to dashboard
  await page.waitForURL('/dashboard', { timeout: 5000 });
}

export async function createInterview(
  page: Page,
  options: {
    interviewType?: string;
    questionCount?: number;
    difficulty?: string;
  } = {}
): Promise<string> {
  // Click "New Interview" button
  await page.click('button:has-text("New Interview")');

  // Fill interview form
  if (options.interviewType) {
    await page.selectOption('select[name="interview_type"]', options.interviewType);
  }
  if (options.questionCount) {
    await page.fill('input[name="question_count"]', options.questionCount.toString());
  }
  if (options.difficulty) {
    await page.selectOption('select[name="difficulty"]', options.difficulty);
  }

  // Submit form
  await page.click('button:has-text("Start Interview")');

  // Wait for redirect to interview page
  await page.waitForURL(/\/interview\/[a-f0-9-]+/, { timeout: 5000 });
  const url = page.url();
  const interviewId = url.split('/').pop() || '';
  return interviewId;
}

export async function waitForApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  timeout = 10000
): Promise<void> {
  await page.waitForResponse(
    (response) => {
      const url = response.url();
      if (typeof urlPattern === 'string') {
        return url.includes(urlPattern);
      }
      return urlPattern.test(url);
    },
    { timeout }
  );
}

export async function waitForToast(page: Page, message: string): Promise<void> {
  await page.waitForSelector(`text=${message}`, { timeout: 5000 });
}

export async function clearLocalStorage(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.clear();
  });
}

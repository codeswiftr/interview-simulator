import { test, expect } from "@playwright/test";

test.describe("Mobile core flows", () => {
  test("visitor can reach dashboard shell", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Welcome back")).toBeVisible();
    await expect(page.getByText("New practice")).toBeVisible();
  });

  test("bottom nav is visible on small viewport", async ({ page }) => {
    await page.goto("/");
    const nav = page.getByRole("navigation");
    await expect(nav).toBeVisible();
    await expect(page.getByText("Practice")).toBeVisible();
    await expect(page.getByText("Home")).toBeVisible();
  });

  test("user can navigate to practice and feedback shells", async ({ page }) => {
    await page.goto("/");
    await page.getByText("Practice").click();
    await expect(page.getByText("Preparation mentor")).toBeVisible();

    await page.getByText("Progress").click();
    await expect(page.getByText("Session feedback")).toBeVisible();
  });

  test("interview room shows state machine controls", async ({ page }) => {
    await page.goto("/interview/test-123");
    await expect(page.getByText("Interview Practice")).toBeVisible();
    // Recording button should appear after permission check
    await expect(
      page.getByRole("button", { name: /start recording|stop recording/i })
    ).toBeVisible({ timeout: 5000 });
  });

  test("preparation page has bottom sheet for Q&A", async ({ page }) => {
    await page.goto("/practice");
    await expect(page.getByText("Ask your mentor")).toBeVisible();
    await page.getByText("Ask your mentor").click();
    await expect(page.getByText("Mentor Q&A")).toBeVisible();
  });

  test("feedback page shows swipeable score cards", async ({ page }) => {
    await page.goto("/feedback/test-123");
    await expect(page.getByText("Overall")).toBeVisible();
    await expect(page.getByText("Content")).toBeVisible();
    await expect(page.getByText("Delivery")).toBeVisible();
    // Cards should be horizontally scrollable
    const scoreSection = page.locator('[class*="overflow-x-auto"]').first();
    await expect(scoreSection).toBeVisible();
  });

  test("dashboard FAB is accessible in thumb zone", async ({ page }) => {
    await page.goto("/dashboard");
    const fab = page.getByRole("button", { name: /start new practice/i });
    await expect(fab).toBeVisible();
    // FAB should be fixed position (check via bounding box)
    const box = await fab.boundingBox();
    expect(box).not.toBeNull();
    // Should be in bottom-right area (thumb zone)
    if (box) {
      expect(box.y).toBeGreaterThan(400); // Near bottom
    }
  });
});

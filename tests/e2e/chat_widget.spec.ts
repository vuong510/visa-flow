/**
 * E2E tests for ChatWidget close button and FAB position fix.
 */
import { test, expect, Page } from "@playwright/test";

const BASE_URL = process.env.BASE_URL || "http://localhost:5173";

test.describe("ChatWidget — close button and FAB position", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    // Wait for page to load
    await expect(page.getByRole("button", { name: /bắt đầu|mở chat|💬/i }).first()).toBeVisible({ timeout: 5000 });
  });

  test("FAB chat button is visible on landing screen", async ({ page }) => {
    const fab = page.locator('button[aria-label*="chat"], button[aria-label*="Mở chat"]');
    await expect(fab).toBeVisible();
  });

  test("clicking FAB opens chat panel", async ({ page }) => {
    await page.locator('button[aria-label*="Mở chat"]').click();
    await expect(page.getByText(/hỏi về visa/i)).toBeVisible();
  });

  test("chat panel header has a close ✕ button", async ({ page }) => {
    await page.locator('button[aria-label*="Mở chat"]').click();
    await expect(page.getByText(/hỏi về visa/i)).toBeVisible();
    // Close button is inside the header
    const closeBtn = page.locator('button[aria-label*="Đóng chat"], button:has-text("✕")');
    await expect(closeBtn).toBeVisible();
  });

  test("close ✕ in header closes the chat panel", async ({ page }) => {
    await page.locator('button[aria-label*="Mở chat"]').click();
    await expect(page.getByText(/hỏi về visa/i)).toBeVisible();
    // Click the ✕ inside the panel header
    await page.locator('button[aria-label*="Đóng chat"], button:has-text("✕")').click();
    await expect(page.getByText(/hỏi về visa/i)).not.toBeVisible();
  });

  test("FAB does not overlap chat send button when open", async ({ page }) => {
    // Open the chat panel
    await page.locator('button[aria-label*="Mở chat"]').click();
    await expect(page.getByText(/hỏi về visa/i)).toBeVisible();

    // Get bounding boxes of the FAB and the send button
    const fab = page.locator('button[aria-label*="Đóng chat"]').or(
      page.locator('button[aria-label*="chat"]').last()
    );
    const sendBtn = page.getByRole("button", { name: /gửi/i });

    const fabBox = await fab.boundingBox();
    const sendBox = await sendBtn.boundingBox();

    if (fabBox && sendBox) {
      // They should NOT overlap — check that there's no intersection
      const fabBottom = fabBox.y + fabBox.height;
      const sendTop = sendBox.y;
      const noVerticalOverlap = fabBottom <= sendBox.y || fabBox.y >= sendBox.y + sendBox.height;
      const noHorizontalOverlap = fabBox.x + fabBox.width <= sendBox.x || fabBox.x >= sendBox.x + sendBox.width;
      expect(noVerticalOverlap || noHorizontalOverlap).toBeTruthy();
    }
  });

  test("Enter key in chat input sends message, not close", async ({ page }) => {
    await page.locator('button[aria-label*="Mở chat"]').click();
    await page.locator('input[placeholder*="câu hỏi"]').fill("xin visa Nhật cần gì?");
    // Pressing Enter should NOT close the panel (old bug: FAB Enter closed chat)
    await page.locator('input[placeholder*="câu hỏi"]').press("Enter");
    // Panel should still be open
    await expect(page.getByText(/hỏi về visa/i)).toBeVisible({ timeout: 2000 });
  });
});

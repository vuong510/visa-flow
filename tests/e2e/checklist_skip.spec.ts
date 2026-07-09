/**
 * E2E tests for ChecklistScreen skip flow + optional badges.
 * Requires the app to be running. Set BASE_URL env var or update below.
 *
 * Run: npx playwright test tests/e2e/checklist_skip.spec.ts
 * (needs: npx playwright install chromium)
 */

import { test, expect, Page } from "@playwright/test";

const BASE_URL = process.env.BASE_URL || "http://localhost:5173";

async function completeFlowToChecklist(page: Page) {
  await page.goto(BASE_URL);

  // LandingScreen — start
  await page.getByRole("button", { name: /bắt đầu/i }).click();

  // DestinationScreen — pick Japan
  await page.getByRole("button", { name: /nhật bản/i }).click();

  // TripFormScreen — enter dates
  await page.getByLabel(/ngày đi/i).fill("2026-09-01");
  await page.getByLabel(/ngày về/i).fill("2026-09-08");
  await page.getByRole("button", { name: /tiếp tục/i }).click();

  // ProfileScreen — employment type
  await page.getByRole("button", { name: /nhân viên/i }).click();

  // Go through remaining profile questions — just click next/continue
  const continueBtn = page.getByRole("button", { name: /tiếp tục|next/i });
  while (await continueBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
    await continueBtn.click();
    await page.waitForTimeout(300);
  }

  // EligibilityScreen — wait for result then continue
  await page.waitForSelector("text=/kết quả|tiếp tục/i", { timeout: 15000 });
  await page.getByRole("button", { name: /tiếp tục/i }).click();

  // PriceScreen — pay demo
  await page.getByRole("button", { name: /thanh toán|tiếp tục/i }).click();

  // Should now be on ChecklistScreen
  await expect(page.getByText(/chuẩn bị hồ sơ/i)).toBeVisible({ timeout: 10000 });
}

test.describe("ChecklistScreen — skip flow", () => {
  test("shows Tôi chưa có button on non-uploaded items", async ({ page }) => {
    await completeFlowToChecklist(page);
    const skipBtns = page.getByRole("button", { name: /tôi chưa có/i });
    await expect(skipBtns.first()).toBeVisible();
  });

  test("clicking skip hides the upload row and shows Bỏ qua + Hoàn tác", async ({
    page,
  }) => {
    await completeFlowToChecklist(page);
    // Skip the first skippable item
    const firstSkip = page.getByRole("button", { name: /tôi chưa có/i }).first();
    await firstSkip.click();
    // Should now show "Bỏ qua" label and "Hoàn tác" button
    await expect(page.getByText(/bỏ qua/i).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /hoàn tác/i }).first()).toBeVisible();
    // Upload button (Tải lên) should also be available on the skipped row
    await expect(page.getByRole("button", { name: /tải lên/i }).first()).toBeVisible();
  });

  test("Hoàn tác restores the normal item row", async ({ page }) => {
    await completeFlowToChecklist(page);
    const firstSkip = page.getByRole("button", { name: /tôi chưa có/i }).first();
    await firstSkip.click();
    await page.getByRole("button", { name: /hoàn tác/i }).first().click();
    // Tôi chưa có should be visible again
    await expect(
      page.getByRole("button", { name: /tôi chưa có/i }).first()
    ).toBeVisible();
  });

  test("skipping all items enables the submit button", async ({ page }) => {
    await completeFlowToChecklist(page);
    // Skip every skippable item (all non-passport items)
    let skipBtns = page.getByRole("button", { name: /tôi chưa có/i });
    while ((await skipBtns.count()) > 0) {
      await skipBtns.first().click();
      await page.waitForTimeout(100);
      skipBtns = page.getByRole("button", { name: /tôi chưa có/i });
    }
    // Submit button should now appear
    await expect(
      page.getByRole("button", { name: /gửi hồ sơ/i })
    ).toBeVisible({ timeout: 3000 });
  });

  test("submitting with skipped required items shows confirm dialog", async ({
    page,
  }) => {
    await completeFlowToChecklist(page);
    let skipBtns = page.getByRole("button", { name: /tôi chưa có/i });
    while ((await skipBtns.count()) > 0) {
      await skipBtns.first().click();
      await page.waitForTimeout(100);
      skipBtns = page.getByRole("button", { name: /tôi chưa có/i });
    }
    // Listen for the confirm dialog
    const dialogPromise = page.waitForEvent("dialog");
    await page.getByRole("button", { name: /gửi hồ sơ/i }).click();
    const dialog = await dialogPromise;
    expect(dialog.message()).toMatch(/chưa tải lên|tài liệu bắt buộc/i);
    await dialog.dismiss(); // Cancel — should stay on page
    await expect(page.getByText(/chuẩn bị hồ sơ/i)).toBeVisible();
  });

  test("optional items show Không bắt buộc badge", async ({ page }) => {
    await completeFlowToChecklist(page);
    // hotel_booking and leave_approval are optional
    const optionalBadges = page.getByText(/không bắt buộc/i);
    await expect(optionalBadges.first()).toBeVisible();
  });
});

test.describe("ChecklistScreen — updated item content", () => {
  test("shows Hành trình bay (not Đặt vé máy bay)", async ({ page }) => {
    await completeFlowToChecklist(page);
    await expect(page.getByText(/hành trình bay/i)).toBeVisible();
    await expect(page.getByText(/đặt vé máy bay/i)).not.toBeVisible();
  });

  test("shows photo size 4.5×3.5cm", async ({ page }) => {
    await completeFlowToChecklist(page);
    await expect(page.getByText(/4\.5.?[×x].?3\.5/i)).toBeVisible();
  });

  test("shows 6 tháng for payslips", async ({ page }) => {
    await completeFlowToChecklist(page);
    // "Bảng lương 6 tháng" should appear
    await expect(page.getByText(/bảng lương.*6.*tháng/i)).toBeVisible();
  });

  test("shows residency_proof item", async ({ page }) => {
    await completeFlowToChecklist(page);
    await expect(page.getByText(/tạm trú|giấy tờ tạm trú/i)).toBeVisible();
  });
});

test.describe("ChecklistScreen — file type validation", () => {
  test("file input accepts only image and PDF", async ({ page }) => {
    await completeFlowToChecklist(page);
    // Check accept attribute on hidden file input
    const acceptAttr = await page
      .locator('input[type="file"]')
      .getAttribute("accept");
    expect(acceptAttr).toContain("image/");
    expect(acceptAttr).toContain("application/pdf");
    expect(acceptAttr).not.toContain(".doc");
  });
});

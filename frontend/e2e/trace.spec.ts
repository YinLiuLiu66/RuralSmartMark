import { expect, test, type Page } from "@playwright/test";

test.beforeAll(async ({ request }) => {
  const response = await request.post("/api/demo/reset");
  expect(response.ok()).toBeTruthy();
});

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
}

test("390px 固定演示码完整展示并记录扫码", async ({ page }) => {
  await page.goto("/trace/ZTDEMO26");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("这箱苹果");
  await expect(page.getByText("固定演示批次").first()).toBeVisible();
  await expect(page.getByAltText("乌蒙丑果包装示意")).toHaveJSProperty("complete", true);
  await expect(page.getByText("山风守园人 看过的园子")).toBeVisible();
  await expect(page.getByText("AI 生成演示插画", { exact: false })).toBeVisible();
  await expect(page.getByText("溢价从哪里来")).toBeVisible();
  await expect(page.getByRole("heading", { name: "问守园人" })).toBeVisible();
  await expect(page.getByText("本码已扫 1 次")).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

test("320px 视口无横向溢出", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 844 });
  await page.goto("/trace/ZTDEMO26");

  await expect(page.getByRole("heading", { level: 1 })).toContainText("这箱苹果");
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await expectNoHorizontalOverflow(page);
});

test("未知码与超长码显示 404 且不溢出", async ({ page }) => {
  await page.goto("/trace/NOPE-404");
  await expect(page.getByRole("heading", { name: "这个码没有记录" })).toBeVisible();
  await expectNoHorizontalOverflow(page);

  await page.goto(`/trace/${"Z".repeat(80)}`);
  await expect(page.getByRole("heading", { name: "这个码没有记录" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

import { expect, test } from "@playwright/test";

test.beforeAll(async ({ request }) => {
  const response = await request.post("/api/demo/reset");
  expect(response.ok()).toBeTruthy();
});

test("工作台展示项目卡，点击进入详情并带上批次", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "我的项目" })).toBeVisible();
  await expect(page.getByText(/\d+ 个项目 · \d+ 个批次/)).toBeVisible();

  const appleCard = page.locator('a[href^="/project/zhaotong-ugly-apple"]');
  const berryCard = page.locator('a[href^="/project/majiang-blueberry-demo"]');
  await expect(appleCard).toBeVisible();
  await expect(berryCard).toBeVisible();

  await appleCard.click();
  await expect(page).toHaveURL(/\/project\/zhaotong-ugly-apple\?batch=\d+/);
  await expect(page.getByRole("combobox").locator("option:checked")).toHaveText(
    "ZT-DEMO-001",
  );
});

test("工作台新建产品只打开总控，不再向会话传目标", async ({ page }) => {
  const bodies: unknown[] = [];
  await page.route("**/api/controller/sessions", async (route) => {
    bodies.push(route.request().postDataJSON());
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: 99,
        product_id: null,
        batch_id: null,
        draft_json: null,
        pending_action_json: null,
        messages: [],
        created_at: "2026-11-13T12:00:00",
        updated_at: "2026-11-13T12:00:00",
      }),
    });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "新建产品" }).click();

  await expect(page.getByPlaceholder(/帮我做贵州麻江蓝莓/)).toBeVisible();
  await expect(page.getByText("工作台 · 未选择项目")).toBeVisible();
  await expect.poll(() => bodies[0]).toEqual({});
});

test("没有包装产出的项目用色块兜底，不出现破图", async ({ page }) => {
  await page.goto("/");
  const berryCard = page.locator('a[href^="/project/majiang-blueberry-demo"]');
  await expect(berryCard).toBeVisible();
  await expect(berryCard.getByText("原料待处理")).toBeVisible();
  await expect(berryCard.locator("img")).toHaveCount(0);
});

import { expect, test } from "@playwright/test";

test.beforeAll(async ({ request }) => {
  const response = await request.post("/api/demo/reset");
  expect(response.ok()).toBeTruthy();
});

test("桌面沙盘加载固定演示批次", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("数据已连接")).toBeVisible();
  await expect(page.getByRole("combobox").locator("option:checked")).toHaveText("ZT-DEMO-001");
  await expect(page.getByText("实时", { exact: true })).toBeVisible();
  await expect(page.getByText("6/6")).toBeVisible();
  await expect(page.getByText("已完成", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("山风守园人").first()).toBeVisible();
  await expect(page.getByText("ZTDEMO26").first()).toBeVisible();
});

test("包装工位展示变体、服务端预览与 IP 插画", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("combobox").selectOption({ label: "ZT-DEMO-001" });

  const stations = page.locator("section", { hasText: "四站点" });
  await stations.getByRole("button", { name: /包装设计/ }).click();

  await expect(page.getByRole("button", { name: "经典牛皮纸" })).toBeVisible();
  await expect(page.getByAltText("包装示意预览")).toHaveJSProperty("complete", true);
  await expect(page.getByAltText("IP 插画（AI 生成）")).toHaveJSProperty("complete", true);

  await page.getByRole("button", { name: "夜绿" }).click();
  await expect(page.getByAltText("包装示意预览")).toHaveAttribute("src", /variant=night/);
});

test("插画生成失败时显示视觉兜底", async ({ page }) => {
  await page.route("**/api/batches/*/workspace", async (route) => {
    const response = await route.fetch();
    const workspace = await response.json();
    workspace.artifacts = workspace.artifacts.map((artifact: Record<string, unknown>) =>
      artifact.kind === "illustration"
        ? {
            ...artifact,
            file_path: null,
            file_url: null,
            content_json: { ...(artifact.content_json ?? {}), error: "测试失败" },
          }
        : artifact,
    );
    await route.fulfill({
      status: response.status(),
      contentType: "application/json",
      body: JSON.stringify(workspace),
    });
  });

  await page.goto("/");
  await expect(page.getByRole("combobox").locator("option:checked")).toHaveText("ZT-DEMO-001");
  const stations = page.locator("section", { hasText: "四站点" });
  await stations.getByRole("button", { name: /包装设计/ }).click();

  await expect(page.getByText("插画这次没有生成")).toBeVisible();
  await expect(page.getByText("包装审核不受影响")).toBeVisible();
});

test("3D 二维码按钮打开溯源 H5", async ({ page, context }) => {
  await page.goto("/");
  await page.getByRole("combobox").selectOption({ label: "ZT-DEMO-001" });
  await expect(page.getByRole("button", { name: "打开溯源页" })).toBeVisible();

  const opened = context.waitForEvent("page");
  await page.getByRole("button", { name: "打开溯源页" }).click();
  const tracePage = await opened;

  await expect(tracePage).toHaveURL(/\/trace\/ZTDEMO26$/);
  await expect(tracePage.getByRole("heading", { level: 1 })).toContainText("这箱苹果");
});

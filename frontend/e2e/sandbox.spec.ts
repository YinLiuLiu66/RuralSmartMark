import { expect, test } from "@playwright/test";

test.beforeAll(async ({ request }) => {
  const response = await request.post("/api/demo/reset");
  expect(response.ok()).toBeTruthy();
});

test("桌面沙盘加载固定演示批次", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("数据已连接")).toBeVisible();
  await expect(page.getByLabel("批次").locator("option:checked")).toHaveText("ZT-DEMO-001");
  await expect(page.getByText("实时", { exact: true })).toBeVisible();
  await expect(page.getByText("6/6")).toBeVisible();
  await expect(page.getByText("已完成", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("山风守园人").first()).toBeVisible();
  await expect(page.getByText("ZTDEMO26").first()).toBeVisible();
});

test("包装工位展示变体、服务端预览与 IP 插画", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("批次").selectOption({ label: "ZT-DEMO-001" });

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
  await expect(page.getByLabel("批次").locator("option:checked")).toHaveText("ZT-DEMO-001");
  const stations = page.locator("section", { hasText: "四站点" });
  await stations.getByRole("button", { name: /包装设计/ }).click();

  await expect(page.getByText("插画这次没有生成")).toBeVisible();
  await expect(page.getByText("包装审核不受影响")).toBeVisible();
});

test("总控面板可打开并显示产品/批次切换", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("combobox").first()).toBeVisible();
  await expect(page.getByRole("combobox").nth(1)).toBeVisible();

  await page.getByRole("button", { name: "打开总控" }).click();
  await expect(page.getByPlaceholder(/帮我做贵州麻江蓝莓/)).toBeVisible();
  await expect(page.getByText("告诉我你想做什么产品", { exact: false })).toBeVisible();
});

test("独立总控页可打开", async ({ page }) => {
  await page.goto("/controller");
  await expect(page.getByPlaceholder(/帮我做贵州麻江蓝莓/)).toBeVisible();
  await expect(page.getByText("调研 · 运行 · 修改 · 审核", { exact: false })).toBeVisible();
});

test("总控先显示用户消息，思维链默认折叠", async ({ page }) => {
  const now = "2026-10-22T12:00:00";
  const session = {
    id: 7,
    product_id: null,
    batch_id: null,
    draft_json: null,
    pending_action_json: null,
    messages: [],
    created_at: now,
    updated_at: now,
  };
  const userMessage = {
    id: 1,
    role: "user",
    content: "你好",
    action_json: null,
    created_at: now,
  };
  const assistantMessage = {
    id: 2,
    role: "assistant",
    content: "你好，我是总控。",
    action_json: { thinking: ["先确认用户意图。", "再回答。"] },
    created_at: now,
  };
  const sse = [
    `data: ${JSON.stringify({ type: "user", message: userMessage })}\n\n`,
    `data: ${JSON.stringify({ type: "thinking", text: "先确认用户意图。\n再回答。" })}\n\n`,
    `data: ${JSON.stringify({ type: "delta", text: "你好，" })}\n\n`,
    `data: ${JSON.stringify({ type: "delta", text: "我是总控。" })}\n\n`,
    `data: ${JSON.stringify({
      type: "done",
      turn: {
        session: { ...session, messages: [userMessage, assistantMessage] },
        reply: "你好，我是总控。",
        questions: [],
        pending_action: null,
        events: [],
        thinking: ["先确认用户意图。", "再回答。"],
      },
    })}\n\n`,
  ].join("");

  await page.route("**/api/controller/sessions**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/messages/stream")) {
      await new Promise((resolve) => setTimeout(resolve, 700));
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: sse,
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(session),
    });
  });

  await page.goto("/controller");
  await page.getByPlaceholder(/帮我做贵州麻江蓝莓/).fill("你好");
  await page.getByRole("button", { name: "发送给总控" }).click();

  await expect(page.getByText("你好", { exact: true })).toBeVisible();
  const summary = page.getByText(/思考过程 · 2 行/);
  await expect(summary).toBeVisible();
  await expect(page.getByText("先确认用户意图。")).toBeHidden();
  await expect(page.getByText("你好，我是总控。")).toBeVisible();

  await summary.click();
  await expect(page.getByText("先确认用户意图。")).toBeVisible();
});

test("3D 二维码按钮打开溯源 H5", async ({ page, context }) => {
  await page.goto("/");
  await page.getByLabel("批次").selectOption({ label: "ZT-DEMO-001" });
  await expect(page.getByRole("button", { name: "打开溯源页" })).toBeVisible();

  const opened = context.waitForEvent("page");
  await page.getByRole("button", { name: "打开溯源页" }).click();
  const tracePage = await opened;

  await expect(tracePage).toHaveURL(/\/trace\/ZTDEMO26$/);
  await expect(tracePage.getByRole("heading", { level: 1 })).toContainText("这箱苹果");
});

import { expect, test } from "@playwright/test";

test.beforeAll(async ({ request }) => {
  const response = await request.post("/api/demo/reset");
  expect(response.ok()).toBeTruthy();
});

test("固定演示批次长时帧率与堆内存", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("批次").selectOption({ label: "ZT-DEMO-001" });
  await expect(page.locator("canvas")).toBeVisible();
  await page.waitForTimeout(3_000);

  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Performance.enable");
  const heapSize = async () => {
    const { metrics } = await cdp.send("Performance.getMetrics");
    return metrics.find((metric) => metric.name === "JSHeapUsedSize")?.value ?? 0;
  };

  const seconds = Number(process.env.PERF_SECONDS ?? 20);
  const heapBefore = await heapSize();
  const fps = await page.evaluate(async (duration) => {
    let frames = 0;
    const started = performance.now();
    await new Promise<void>((resolve) => {
      const tick = (now: number) => {
        frames += 1;
        if (now - started >= duration) resolve();
        else requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
    return frames / ((performance.now() - started) / 1000);
  }, seconds * 1000);
  const heapAfter = await heapSize();

  console.log(
    `fps=${fps.toFixed(1)} heap=${(heapBefore / 1024 / 1024).toFixed(1)}MB -> ${(
      heapAfter /
      1024 /
      1024
    ).toFixed(1)}MB`,
  );
  expect(fps).toBeGreaterThanOrEqual(45);
  expect(heapAfter - heapBefore).toBeLessThan(30 * 1024 * 1024);
});

test("200% 等效视口回退为桌面提示且不横向溢出", async ({ page }) => {
  await page.setViewportSize({ width: 640, height: 360 });
  await page.goto("/");

  await expect(page.getByText(/3D 沙盘需要桌面端/)).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
});

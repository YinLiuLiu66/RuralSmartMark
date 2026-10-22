# 智农云链 v2 · frontend

React 19 + TypeScript + Vite + React Three Fiber + Zustand + Tailwind CSS v4。

```bash
cd frontend
pnpm install
pnpm dev        # http://127.0.0.1:5173
pnpm typecheck
pnpm lint
pnpm build
pnpm exec playwright install chromium   # 首次
pnpm test:e2e                           # 10 条冒烟
pnpm test:perf                          # 60 秒性能
```

`/api` 由 Vite 代理到 `http://127.0.0.1:8000`。页面：

- `/` 桌面沙盘：产品/批次切换、3D、站点卡、总控抽屉
- `/controller` 独立总控：流式回复、思维链折叠、调研建档、修改、通过、回退
- `/trace/:code` 移动端溯源 H5（固定演示码 `ZTDEMO26`）

Playwright 配置在 `playwright.config.ts`，冒烟/性能用例在 `e2e/`；服务未启动时会自动迁移、seed 并拉起前后端。设计契约与 token 见 `docs/v2/ui.md`；总控契约见 `docs/v2/controller.md`；方案见 `docs/v2/plan.md`；现场操作见 `docs/v2/runbook.md`。

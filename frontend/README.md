# 乡土印记 v2 · frontend

React 19 + TypeScript + Vite + React Three Fiber + Zustand + Tailwind CSS v4。

```bash
cd frontend
pnpm install
pnpm dev        # http://127.0.0.1:5173
pnpm typecheck
pnpm lint
pnpm build
pnpm exec playwright install chromium   # 首次
pnpm test:e2e                           # 6 条冒烟
pnpm test:perf                          # 60 秒性能
```

`/api` 由 Vite 代理到 `http://127.0.0.1:8000`。页面：

- `/` 桌面沙盘（固定演示批次 `ZT-DEMO-001`；3D 需 ≥1024px）
- `/trace/:code` 移动端溯源 H5（固定演示码 `ZTDEMO26`）

Playwright 配置在 `playwright.config.ts`，冒烟/性能用例在 `e2e/`；服务未启动时会自动迁移、seed 并拉起前后端。设计契约与 token 见 `docs/v2/ui.md`；方案见 `docs/v2/plan.md`；现场操作见 `docs/v2/runbook.md`。

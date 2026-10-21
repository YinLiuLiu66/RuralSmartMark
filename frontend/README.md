# 乡土印记 v2 · frontend

React 19 + TypeScript + Vite + React Three Fiber + Zustand + Tailwind CSS v4。

```bash
cd frontend
pnpm install
pnpm dev        # http://127.0.0.1:5173
pnpm typecheck
pnpm lint
pnpm build
```

`/api` 由 Vite 代理到 `http://127.0.0.1:8000`。页面：

- `/` 桌面沙盘（Phase 0：数据层 + 最小 3D 场景）
- `/trace/:code` 移动端溯源骨架（Phase 3 接入）

设计契约与 token 见 `docs/v2/ui.md`；方案见 `docs/v2/plan.md`。

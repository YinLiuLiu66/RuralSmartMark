# RuralSmartMark Frontend

React 18 + Vite + TypeScript。运行说明见仓库根目录 [README](../README.md)。

## 快速开始

```bash
cd frontend
pnpm install
pnpm dev        # http://localhost:5173
```

## 与后端联调

`vite.config.ts` 已配置代理，`/api/*` 会转发到 `http://127.0.0.1:8000`，
前提是后端已启动且监听 8000 端口。

如需指向其他后端地址，在 `.env` 中设置：

```bash
VITE_API_BASE_URL=https://api.example.com
```

留空则走同源（即代理）。

## 常用命令

| 命令 | 说明 |
| --- | --- |
| `pnpm dev` | 启动开发服务 |
| `pnpm build` | 类型检查 + 生产构建 |
| `pnpm preview` | 预览 `dist/` |
| `pnpm lint` | oxlint 检查 |
| `pnpm typecheck` | 仅类型检查 |

# RuralSmartMark

前后端分离项目。

- **backend** — FastAPI + Python 3.13，依赖用 [uv](https://docs.astral.sh/uv/) 管理
- **frontend** — React 18 + Vite + TypeScript，包管理用 [pnpm](https://pnpm.io/)

## 目录结构

```
RuralSmartMark/
├── backend/
│   ├── src/ruralsmartmark/
│   │   ├── app.py        # FastAPI 实例、CORS、路由
│   │   ├── config.py     # pydantic-settings 配置
│   │   └── main.py       # 启动入口（uvicorn）
│   ├── tests/
│   ├── .env.example
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── api/client.ts # 请求封装
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── .env.example
│   ├── package.json
│   ├── pnpm-lock.yaml
│   └── vite.config.ts
└── README.md
```

## 环境要求

| 工具 | 版本 |
| --- | --- |
| Python | >= 3.13 |
| uv | >= 0.13 |
| Node.js | >= 20.19 |
| pnpm | >= 10 |

## 快速开始

### 后端

```bash
cd backend
uv sync
cp .env.example .env      # 填写 OPENAI_API_KEY 等
uv run ruralsmartmark     # http://127.0.0.1:8000
```

交互式 API 文档：<http://127.0.0.1:8000/docs>

### 前端

```bash
cd frontend
pnpm install
pnpm dev                  # http://localhost:5173
```

前端通过 `vite.config.ts` 中的代理把 `/api/*` 转发到 `http://127.0.0.1:8000`，
开发期不需要额外处理跨域。

## 常用命令

| 位置 | 命令 | 说明 |
| --- | --- | --- |
| backend | `uv run ruralsmartmark` | 启动开发服务（热重载） |
| backend | `uv run pytest` | 运行测试 |
| backend | `uv run ruff check .` | 静态检查 |
| backend | `uv run ruff format .` | 格式化 |
| frontend | `pnpm dev` | 启动开发服务 |
| frontend | `pnpm build` | 类型检查 + 生产构建 |
| frontend | `pnpm lint` | oxlint 检查 |
| frontend | `pnpm preview` | 预览生产构建产物 |

## 接口约定

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |

业务接口统一挂在 `/api` 前缀下，方便前端代理和反向代理规则收敛。

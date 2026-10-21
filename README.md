# RuralSmartMark

前后端分离项目。AI 协作者请先阅读根目录 [AGENTS.md](AGENTS.md) 与
[docs/05-next-steps.md](docs/05-next-steps.md)。

- **backend** — FastAPI + Python 3.13，依赖用 [uv](https://docs.astral.sh/uv/) 管理
- **frontend** — React 18 + Vite + TypeScript，包管理用 [pnpm](https://pnpm.io/)

## 文档（设计讨论的记分板）

| 文档 | 内容 |
| --- | --- |
| [docs/00-project-brief.md](docs/00-project-brief.md) | 项目定位、背景与核心叙事 |
| [docs/01-architecture.md](docs/01-architecture.md) | 技术架构、目录结构与选型 |
| [docs/02-agents.md](docs/02-agents.md) | 五个 AI Agent 的职责与优先级 |
| [docs/03-data-model.md](docs/03-data-model.md) | 数据模型与接口约定 |
| [docs/04-roadmap.md](docs/04-roadmap.md) | MVP 切分与里程碑 |
| [docs/05-next-steps.md](docs/05-next-steps.md) | 下一步任务清单（当前执行进度） |
| [docs/decisions.md](docs/decisions.md) | 决策记录（已定/待定清单） |

## 目录结构

```
RuralSmartMark/
├── docker-compose.yml    # 单 db 服务（PG18 + pgvector，数据落 ./data/postgres/）
├── backend/
│   ├── src/ruralsmartmark/
│   │   ├── app.py        # FastAPI 实例、CORS、路由
│   │   ├── config.py     # pydantic-settings 配置
│   │   ├── db.py         # async engine/sessionmaker 单例
│   │   ├── auth.py       # JWT 双角色鉴权
│   │   ├── models/       # 14 张表 ORM
│   │   ├── routes/       # APIRouter 模块
│   │   ├── seed.py       # 演示账号 seed（python -m ruralsmartmark.seed）
│   │   └── main.py       # 启动入口（uvicorn）
│   ├── migrations/       # Alembic 迁移
│   ├── tests/
│   ├── .env.example
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── api/client.ts # 请求封装
│   │   ├── three/        # 3D 沙盘（M0 探针，报告见 docs/05-probe-r3f.md）
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
| Docker | compose v2 |

## 快速开始

### 数据库（前置，仓库根目录执行）

```bash
docker compose up -d       # PG18 + pgvector，数据落 ./data/postgres/
```

### 后端

```bash
cd backend
uv sync
cp .env.example .env       # 填写 OPENAI_API_KEY 等
uv run alembic upgrade head           # 建 14 张表
uv run python -m ruralsmartmark.seed  # 种演示账号 operator/coop
uv run python -m ruralsmartmark.agents.pregenerate  # 可选：预生成故事/文案（断网演示）
uv run ruralsmartmark      # http://127.0.0.1:8000
```

交互式 API 文档：<http://127.0.0.1:8000/docs>

### 前端

```bash
cd frontend
pnpm install
pnpm dev                  # http://localhost:5173（`/` 沙盘，`/workbench` Agent 工作台）
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

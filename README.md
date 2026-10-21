# 乡土印记 v2 · RuralSmartMark

县域农产品的 AI 品牌流水线：一个产品批次从田间走到消费者，四个 Agent 完成**故事/IP → 包装设计 → 内容营销 → 定价/溯源**；3D 沙盘可视化整条流水线，消费者扫码看溯源 H5。

首个案例：**昭通丑苹果**（云南省昭通市昭阳区）。区域事实可查；合作社、品牌名与人物为演示合成。

## 当前状态（2026-10-21）

**Phase 0 已完成**：

- `rewrite/v2` 分支；旧 v1 代码移出工作树（`main` 保留历史）。
- FastAPI + SQLite（9 张表）+ Alembic 初始迁移 + 幂等 seed。
- Mock LLM / Image Provider；无 `OPENAI_API_KEY` 也能跑。
- 前端 React 19 + R3F 9 + Tailwind 4：桌面沙盘骨架、果园/四站点/批次/卡车、移动端溯源骨架。
- 后端 4 测试、ruff、前端 typecheck/lint/build 全绿；1280×720 与 390×844 视觉验收通过。

**Phase 1 下一步**：mock 四 Agent 流水线、人工审核、SSE、站点卡、批次移动。真实 Agent / 溯源 API / 包装合成 / 定价计算尚未实现。

## 快速开始

环境：Python ≥ 3.13、uv ≥ 0.13、Node ≥ 20.19、pnpm ≥ 10。**不需要 Docker/Postgres。**

### 后端

```bash
cd backend
cp .env.example .env      # 首次；已有 .env 跳过；OPENAI_API_KEY 可空，空则 Mock
uv sync
uv run alembic upgrade head
uv run python -m ruralsmartmark.seed
uv run ruralsmartmark     # http://127.0.0.1:8000
```

### 前端

```bash
cd frontend
pnpm install
pnpm dev                  # http://127.0.0.1:5173
```

- 桌面沙盘：<http://127.0.0.1:5173/>
- 溯源骨架：<http://127.0.0.1:5173/trace/ZTDEMO26>
- API 文档：<http://127.0.0.1:8000/docs>

Vite 已把 `/api` 代理到 `127.0.0.1:8000`。

## 目录结构

```
backend/
  src/ruralsmartmark/       # FastAPI 应用、ORM、routes、providers、seed
  migrations/               # Alembic
  tests/                    # health / seed / batches
frontend/
  src/three/                # R3F 等距场景
  src/routes/               # Sandbox / Trace
  src/stores/               # Zustand
  src/styles/               # Tailwind v4 + 山野编辑部 token
docs/
  decisions.md              # 决策（v1 #1–#31 + v2 #32 起）
  v2/plan.md                # v2 产品/架构方案
  v2/ui.md                  # 前端设计契约
  v2/sources.md             # 昭通事实待核验清单
  05-next-steps.md          # 当前进度与下一步
```

## 常用命令

| 位置 | 命令 | 说明 |
| --- | --- | --- |
| backend | `uv run ruralsmartmark` | 启动开发服务（热重载） |
| backend | `uv run pytest` | 后端测试（临时 SQLite） |
| backend | `uv run ruff check .` | 静态检查 |
| backend | `uv run alembic upgrade head` | 迁移 |
| backend | `uv run python -m ruralsmartmark.seed` | 幂等 seed |
| frontend | `pnpm dev` | 开发服 |
| frontend | `pnpm typecheck` / `pnpm lint` / `pnpm build` | 前端检查/构建 |

## 接口（Phase 0）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查（含 DB） |
| GET | `/api/products` | 产品档案 |
| GET | `/api/batches` | 批次列表 |
| POST | `/api/batches` | 新建批次 |
| GET | `/api/batches/{id}` | 批次详情 |
| GET | `/api/batches/by-code/{code}` | 按批次码查 |
| POST | `/api/demo/reset` | 重置演示批次 |

## 设计方向

- 「山野编辑部」：暖色纸感、衬线标题、低多边形乡村；不是 WMS 冷色控制塔。
- 3D 构建对齐 WareTrack：代码拼低多边形几何体 + 平面材质 + CanvasTexture；不引 GLB/写实资产。
- 桌面看 3D 沙盘，手机只看扫码溯源 H5。
- 不做游戏化、多产品 UI、登录/权限、真实电商 API、Canva/Midjourney、IoT 温度曲线。

## 文档

- [AGENTS.md](AGENTS.md) — AI 协作约束（人类可跳过）
- [docs/v2/plan.md](docs/v2/plan.md) — 完整方案
- [docs/v2/ui.md](docs/v2/ui.md) — 前端设计契约
- [docs/v2/sources.md](docs/v2/sources.md) — 昭通事实待核验清单
- [docs/decisions.md](docs/decisions.md) — 决策记录
- [docs/05-next-steps.md](docs/05-next-steps.md) — 当前进度与下一步

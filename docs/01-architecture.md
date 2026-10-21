# 01 · 架构设计

> 状态：✅ 主干定稿 — M1–M6 落地后目录结构与运行方式已同步实测形态
> 更新时间：2026-10-21

## 1. 总体架构

```
┌───────────────────────────  前端 (React 18 + Vite + TS)  ───────────────────────────┐
│  3D 沙盘 (React Three Fiber)   Agent 工作台   数据看板 (ECharts)   溯源 H5 (/t/:code) │
└───────────────▲──────────────────────────────────────────▲─────────────────────────┘
                │ WebSocket（实时状态流）                    │ REST（查询 / 指令）
┌───────────────┴──────────────────────────────────────────┴─────────────────────────┐
│                                 后端 (FastAPI + Python 3.13)                        │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────┐  ┌────────────┐  ┌─────────────┐  │
│  │ 模拟引擎  │  │  Agent 编排  │  │  业务 service │  │  ws 事件总线│  │  auth (JWT) │  │
│  │  (sim)   │  │  (agents)    │  │  (services)  │  │  (ws)      │  │             │  │
│  └────▲─────┘  └──────▲───────┘  └──────▲───────┘  └─────▲──────┘  └─────────────┘  │
│       │ tick 驱动      │ 调用 LLM         │               │                          │
│  ┌────┴────────────────┴─────────────────┴───────────────┴────────────────────────┐  │
│  │        PostgreSQL 18 (asyncpg + SQLAlchemy 2.0 + Alembic + pgvector预留)        │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. 关键设计决策

| 决策点 | 结论 | 理由 |
| --- | --- | --- |
| 数据库 | PostgreSQL 18（镜像 `pgvector/pgvector:pg18`），SQLAlchemy 2.0 异步 | pgvector 已支持 18，见 decisions #18；知识库检索暂不启用（pgvector 预留），不另引向量库 |
| 实时推送 | WebSocket 只发增量；全量快照走 REST `GET /api/world/snapshot` | 3D 沙盘需高频状态流；主从分工见 decisions #17 |
| Agent 编排 | 手写（**不引 LangChain**） | 5 个 Agent 工作流清晰，手写更可控、答辩讲得清 |
| 常驻任务 | asyncio 后台任务（**不引 Celery/Redis**） | 演示型项目，后期需要再加 |
| 鉴权 | 简单 JWT，双角色（运营方/合作社） | 约 1 天工作量，答辩有支撑 |
| LLM 接入 | 国内 OpenAI 兼容端点（智谱/通义/DeepSeek），配置切换 | 网络稳、成本低 |
| 3D 素材 | 纯几何体程序化拼装 low-poly | 零美术依赖，出效快；关键物件后期可换 GLB |
| 模拟引擎 | 可重放固定剧本（参数化随机 + 可选固定 seed） | 答辩演示可控、可复现 |

## 3. 后端目录结构（规划）

```
backend/src/ruralsmartmark/
├── main.py / app.py / config.py     # 已有；app.py lifespan 托管 sim 引擎主循环
├── db.py                            # async engine + session
├── models/                          # SQLAlchemy 2.0 ORM 实体（见 03 文档）✅ 已建
│   ├── base.py / runtime.py / business.py / auth.py
├── routes/                          # 路由层（auth/sim/world/agents/trace/pricing，新资源按文件加）
│   ├── trace.py                     # 公开溯源接口 /api/trace/{code}（M5，#30）
│   └── pricing.py                   # 公开溢价对照 /api/pricing/benchmarks（M6，#31）
├── schemas/                         # Pydantic 请求/响应（M4 agents / M5 trace / M6 pricing）
├── agents/                          # ⭐ M4：手写 LLM 编排（decisions #6）
│   ├── llm.py          # OpenAI 兼容封装（AsyncOpenAI；空 key 走 mock）
│   ├── prompts.py      # 故事/文案 Prompt 集中管理
│   ├── context.py      # 从 DB 取运营事实注入 Prompt（#27）
│   ├── pregenerate.py  # 预生成故事/文案定稿入库（#11）
│   └── materials/      # 固定素材包（麻江县·蓝莓，#28）
├── sim/                             # ⭐ 模拟引擎内核 ✅ 已建（M2）
│   ├── clock.py          # 虚拟时钟：tick=1 模拟分钟，可暂停/变速/重置
│   ├── engine.py         # SimEngine：lifespan 托管主循环，落库→广播
│   ├── state_machines.py # 运单五步/车辆四态/worker 枚举
│   └── scenario.py       # 剧本：初始世界生成 + 双写 + 事件拼装 + 固定演示溯源（#30）
├── ws/                              # WebSocket 通道 + 事件总线 ✅ 已建（M2）
│   └── bus.py            # EventBus：全体广播不区分角色（decisions #19）
├── seed.py                          # 演示账号（幂等）
└── auth.py                          # JWT 签发/校验、双角色依赖
```

**运行方式**：uvicorn lifespan 拉起 `sim` 的 asyncio 主循环（后端重启 = 演示起点），
每 tick（= 模拟 1 分钟，默认 2 倍速）推进剧本 → 变更落库 → 事件广播到 WebSocket；
**先落库成功再广播**（05 M2 铁律）。模拟时间与真实时间分离：trace/telemetry/运单时点
一律写模拟时间。Agent 长任务（M4）走 asyncio 后台任务，进度经同一事件总线推送。

## 4. 前端目录结构（M5 起三页：`/` 沙盘 + `/workbench` 工作台 + `/t/:code` 溯源）

```
frontend/src/
├── api/                # 按资源拆模块
│   ├── client.ts       # fetch 封装 + ApiError（M3 快照/控制，M4 登录态）
│   ├── agents.ts       # Agent 任务 REST（M4）
│   ├── pricing.ts      # 公开溢价对照 REST（M6）
│   ├── trace.ts        # 公开溯源 REST + 固定演示码（M5）
│   ├── types.ts        # 快照/WS/Agent/溯源类型 ✅
│   └── ws.ts           # /ws/world WS 客户端 + 自动重连 ✅ 已建
├── stores/             # Zustand：实体状态、选中对象、模拟时钟
│   ├── world.ts        # 沙盘实时态：快照打底 + WS 增量合并 ✅ 已建
│   └── auth.ts         # 登录态 token/role/username（M4）
├── components/         # TopNav / LoginDialog / ArtifactEditor（M4）/ TraceQrCard（M5）/ PricingCard（M6）
├── panels/             # 模板化详情卡
│   └── ClockBar.tsx    # 模拟时钟控制条 ✅ 已建（站点/车辆/托盘卡在 three/DetailCard.tsx）
├── routes/             # react-router（M4 起启用，decisions #24）
│   ├── Sandbox.tsx     # ⭐ 主页面：3D 沙盘 + 环绕看板 + 详情卡 + 溢价卡（M3 迁入 / M6 扩展）
│   ├── AgentWorkbench.tsx # Agent 任务列表 + 产出物审阅/润色（M4）
│   └── Trace.tsx       # /t/:code 扫码 H5 + Trace.css（M5）
└── three/              # R3F：Scene / entities/*（站点、冷链车、托盘）✅ M3 已建
```

看板图表用 ECharts；大屏风格走自定义 CSS（玻璃拟态），不套 Antd 后台风。
状态管理定稿：TanStack Query（REST 缓存 + WS 事件失效）+ Zustand（沙盘实时态），见 decisions #8/#24。

## 5. 基础设施

- **docker compose**：M1 先起单 `db` 服务（`pgvector/pgvector:pg18`，数据卷挂 `/var/lib/postgresql`，18 起官方镜像路径变更）；后端进 compose 后期补，前端开发期走 pnpm dev
- **环境变量**：`DATABASE_URL`、`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`（文本模型 `deepseek-ai/DeepSeek-V3.1-Terminus`，decisions #23）、`JWT_SECRET`、`SIM_SEED`（可选固定剧本种子）
- **CI/质量**：后端 ruff + pytest；前端 oxlint + tsc（沿用现状）

## 6. 待定问题（需拍板后更新本文档）

- [ ] 3D 场景的具体交互细节（相机动画、选择高亮的表现形式）——随 M3 定
- 其余选型均已定稿，见 [decisions.md](./decisions.md)：状态库 #8、溯源深度 #9、sim 控制与快照主从 #17、pgvector 处置 #18

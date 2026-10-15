# 01 · 架构设计

> 状态：🔶 草案 — 主干已定，细节待补
> 更新时间：2026-10-14

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
│  │        PostgreSQL 16+ (asyncpg + SQLAlchemy 2.0 + Alembic + pgvector)          │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. 关键设计决策

| 决策点 | 结论 | 理由 |
| --- | --- | --- |
| 数据库 | PostgreSQL 16+，SQLAlchemy 2.0 异步 | 用户已确认；知识库检索用 pgvector，不另引向量库 |
| 实时推送 | WebSocket | 3D 沙盘需高频状态流 |
| Agent 编排 | 手写（**不引 LangChain**） | 5 个 Agent 工作流清晰，手写更可控、答辩讲得清 |
| 常驻任务 | asyncio 后台任务（**不引 Celery/Redis**） | 演示型项目，后期需要再加 |
| 鉴权 | 简单 JWT，双角色（运营方/合作社） | 约 1 天工作量，答辩有支撑 |
| LLM 接入 | 国内 OpenAI 兼容端点（智谱/通义/DeepSeek），配置切换 | 网络稳、成本低 |
| 3D 素材 | 纯几何体程序化拼装 low-poly | 零美术依赖，出效快；关键物件后期可换 GLB |
| 模拟引擎 | 可重放固定剧本（参数化随机 + 可选固定 seed） | 答辩演示可控、可复现 |

## 3. 后端目录结构（规划）

```
backend/src/ruralsmartmark/
├── main.py / app.py / config.py     # 已有；config 需加 DATABASE_URL 等
├── db.py                            # async engine + session
├── models/                          # SQLAlchemy 2.0 ORM 实体（见 03 文档）
├── schemas/                         # Pydantic 请求/响应模型
├── api/                             # 路由层（按资源分文件：auth/site/vehicle/...）
├── services/                        # 业务逻辑（路由只做校验+调用）
├── sim/                             # ⭐ 模拟引擎内核
│   ├── clock.py          # 虚拟时钟：tick 驱动，可暂停/变速/重置
│   ├── world.py          # 世界状态：站点/车辆/托盘/运单的实体容器
│   ├── state_machines.py # Truck: En route→Docking→Unloading→Departed 等
│   └── scenario.py       # 剧本：初始世界生成 + 事件脚本
├── agents/                          # Agent 编排层（见 02 文档）
├── ws/                              # WebSocket 通道 + 事件总线
└── auth/                            # JWT 签发/校验、双角色依赖
```

**运行方式**：uvicorn 启动时拉起 `sim` 的 asyncio 主循环，每个 tick（= 模拟时间 1 分钟，默认加速播放）推进状态机 → 变更落库 → 事件广播到 WebSocket。Agent 长任务走 asyncio 后台任务，进度经同一事件总线推送。

## 4. 前端目录结构（规划）

```
frontend/src/
├── api/                # 已有 client.ts，按资源拆模块
├── routes/             # react-router
│   ├── Sandbox/        # ⭐ 主页面：3D 沙盘 + 环绕看板 + 详情卡
│   ├── AgentWorkbench/ # Agent 任务列表 + 产出物审阅/润色（人机协同演示位）
│   └── Trace/          # /t/:code 扫码 H5（移动端优先，独立无壳布局）
├── three/              # R3F：Scene / CameraRig / entities/*（站点、冷链车、托盘）
├── ws/                 # WS 客户端：快照 + 增量，合并进状态库
├── stores/             # Zustand：实体状态、选中对象、模拟时钟
└── panels/             # 模板化详情卡（站点卡/车辆卡/托盘卡/运单卡）
```

看板图表用 ECharts；大屏风格走自定义 CSS（玻璃拟态），不套 Antd 后台风。

## 5. 基础设施

- **docker compose**：`db`（PostgreSQL）+ 后端 + 前端（后期补）
- **环境变量**：`DATABASE_URL`、`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`、`JWT_SECRET`、`SIM_SEED`（可选固定剧本种子）
- **CI/质量**：后端 ruff + pytest；前端 oxlint + tsc（沿用现状）

## 6. 待定问题（需拍板后更新本文档）

- [ ] 状态库：TanStack Query + Zustand（我方默认）vs 纯 Zustand
- [ ] 3D 场景的具体交互细节（相机动画、选择高亮的表现形式）
- [ ] 溯源 H5 是否要"与 IP 角色实时对话"的能力（见 decisions.md #7）

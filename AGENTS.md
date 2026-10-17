# AGENTS.md

本文件只供 AI Agent 阅读，人类读者请看 README.md。两者内容不重复、不冲突。

## 项目定位

- 「挑战杯」竞赛演示项目：县域农产品的 AI 品牌化 + 3D 数字孪生供应链。
- 正确性优先级：演示动线完整可复现 > 演示效果好看 > 代码整洁 > 生产运维（并发/真实数据）。
- 面向人的界面与文案一律用中文；代码注释允许中英混排但不写"怎么调/做什么"类废话。
- 任何架构层取舍，动手前必须先在 docs/decisions.md 里找到对应编号条目；冲突时以其最新条目为准。

## 环境特殊性（缺就是缺，别假设有）

- 包管理器只用 uv（后端）+ pnpm（前端），不存在 requirements.txt 与 package-lock；
  uv ≥ 0.13，Python ≥ 3.13，Node ≥ 20.19，pnpm ≥ 10。uv 安装：docs.astral.sh/uv，pnpm 安装：pnpm.io/zh/installation。
- 后端缺 `backend/.env` 时靠默认值能起（DATABASE_URL 有默认指向 127.0.0.1:5432 的本地库），
  但 LLM / 数据库连接不可用；先 `cp backend/.env.example backend/.env` 并 `docker compose up -d`。
- OPENAI_API_KEY 为空时：真调模型的路径不能实测，一律 mock，别假设 key 存在。
- 前端没有测试框架，只有 `pnpm typecheck` / `pnpm lint` 兜底；别假设存在 vitest / jest。
- M2 起：`uv run ruralsmartmark` 会用 lifespan 拉起 sim 引擎主循环（默认 2 倍速）；TestClient
  测试不触发 lifespan，测试里真实推进需显式驱动（见 tests/test_sim.py 的模式）。

## 常用命令（后端在 backend/ 下，前端在 frontend/ 下）

- Docker（仓库根目录执行）：
  `docker compose up -d` → 起 PG18 数据库（rsm-postgres 容器，127.0.0.1:5432；数据落 `./data/postgres/`）
- 后端（uv，在 backend/）：
  `uv sync` → 依赖安装（别手动建 venv）
  `uv run alembic upgrade head` → 建表/迁移（M1 起有效；downgrade base 可回滚重放）
  `uv run python -m ruralsmartmark.seed` → 种演示双账号 operator/coop（幂等）
  `uv run ruralsmartmark` → 起服务，端口 8000
  `uv run pytest` → 全测试；单函数：`uv run pytest tests/test_health.py::test_health`
  `uv run ruff check .` → 静态检查；`uv run ruff format .` → 格式化
- 前端（pnpm，在 frontend/）：
  `pnpm install` → 依赖
  `pnpm dev` → 开发服，端口 5173
  `pnpm build` / `pnpm typecheck` / `pnpm lint`
- 文档本身无构建步骤，直接 git 改 `.md`。

## 目录地图（改哪去哪，产物别碰）

```
docker-compose.yml                 # 单 db 服务（pgvector/pgvector:0.8.7-pg18，卷挂 ./data/postgres）
backend/
  src/ruralsmartmark/app.py         # 路由注册 + lifespan（拉起/停止 sim 引擎主循环）
  src/ruralsmartmark/config.py      # pydantic-settings：新配置项加进 Settings 类
  src/ruralsmartmark/main.py        # uvicorn 入口（ruralsmartmark 命令绑这）
  src/ruralsmartmark/db.py          # async engine + sessionmaker 单例 + get_session 依赖
  src/ruralsmartmark/auth.py        # JWT 双角色（get_current_user / require_role）
  src/ruralsmartmark/models/        # 14 张表 ORM（runtime/business/auth 三文件，__init__ 汇总）
  src/ruralsmartmark/routes/        # APIRouter 模块（auth / sim / world）
  src/ruralsmartmark/sim/           # M2 模拟引擎：clock（虚拟时钟）/ engine（主循环）/ state_machines / scenario（剧本：初始世界 + 双写）
  src/ruralsmartmark/ws/            # ws/bus.py：EventBus 全体广播（不区分角色，decisions #19）
  src/ruralsmartmark/seed.py        # 演示数据 seed（python -m ruralsmartmark.seed）
  migrations/                       # Alembic（生成物，ruff 不检；env.py 接 Settings/ORM）
  tests/conftest.py                 # 测试夹具：独立测试库 _test + NullPool（跨循环必需）
  tests/test_auth.py                # 401/403/200 全路径
  tests/test_sim.py                 # M2 验收：控制/快照/WS + 一完整周期双写推进
  pyproject.toml                    # 依赖 + ruff + pytest 配置
frontend/
  src/api/client.ts                 # fetch 封装 + ApiError + snapshot/simControl 接口
  src/api/types.ts                  # 世界快照与 WS 事件封套类型（与 docs/03 §3 对齐）
  src/api/ws.ts                     # WS 客户端（相对 URL 推导 + 指数退避重连）
  src/stores/world.ts               # Zustand 沙盘实时态：快照打底 + WS 增量合并
  src/panels/ClockBar.tsx           # 模拟时钟控制条（operator 按钮，decisions #17）
  src/three/WorldScene.tsx          # 正式 3D 场景（吃 M2 快照/WS 数据）
  src/three/SiteMeshes.tsx          # 站点网格（库存映射高度，可点选）
  src/three/VehicleMesh.tsx         # 车辆网格（在途插值/停靠，可点选）
  src/three/DetailCard.tsx          # 详情卡（站点/车辆/运单 stepper）
  src/three/FpsBadge.tsx            # rAF 帧率徽章
  src/App.tsx / App.css             # 沙盘主页壳（含 stepper 等样式）
  vite.config.ts                    # /api 与 /ws（ws:true）→ 127.0.0.1:8000 开发代理
docs/
  decisions.md                      # 决策权威：拍板条目唯一真源
  00–04*.md                         # 设计权威：架构 / 数据模型 / 路线图
  05-next-steps.md                  # 唯一动态任务清单：进度与未验证假设
  05-probe-r3f.md                   # M0 探针报告（3D 路线结论 + 踩坑，M3 依赖）
```

尚未创建、创建前勿假设存在：backend 的 agents/ / schemas/，frontend 的 routes/ 等
（规划见 docs/01-architecture.md）。
子目录若有专属强约定，另建 `<dir>/AGENTS.md`，根文件只引用不复制。

## 文档维护职责（必读必做）

核心原则：文档与代码一旦产生偏差，要么立刻修文档，要么立刻报告差异，不许含糊带过。
每条事实只允许在一处权威定义，其他位置一律引用路径，禁止复制正文。

| 文档 | 权威范围 | Agent 必做的维护 |
| --- | --- | --- |
| AGENTS.md | 操作事实：命令 / 环境 / 目录 / 红线 | 改动命令、目录、依赖、端口、env、测试方式后**必须同步本文件**；过时行直接删 |
| docs/decisions.md | 决策权威：唯一真源 | 任何拍板（含"暂不解决"）先新增 #N 编号条目，再同步设计文档；不删号、不重排 |
| docs/00–04*.md | 设计静态权威 | 仅当被新决策推翻时改对应小节 + 更新文首日期；无因不改 |
| docs/05-next-steps.md | 唯一动态任务清单 | 开工前拆块写条目与假设；完工立即在"当前进度"打勾；发现新假设补录"未验证假设" |
| README.md | 人类读者入口 | 运行方式 / 目录结构变化时同步；不复制 AGENTS.md 的约束 |

自检句式：**"删了这条，新 Agent 是否会犯明显错？"** 会才写，不会就删。
新会话验证：让一个只读本文件 + 05-next-steps.md 的裸 Agent 走完"装环境 → 跑命令 → 改文档"全流程，
哪一步卡壳，哪一步就是文档的缺失或过时处，当场修。

## 红线

- 不引入 decisions.md 任一被否决的方案：LangChain / LlamaIndex / Celery / Redis / Chroma。
- 不提交 .env、dist/、node_modules/ 等被 .gitignore 覆盖的产物；改 .gitignore 需要充分理由。
- 不使用 `/var/lib/postgresql/data` 做容器内数据卷挂载点（PG18 正确路径为 `/var/lib/postgresql`，真实 PGDATA 在其下 `18/docker`）；
  本地宿主机侧卷落点为项目目录 `./data/postgres`（decisions #20，已 ignore）。
- 不对 README / docs 做结构性改动而不同步 AGENTS.md 或 docs/05-next-steps.md。
- 无法核实的事实（假设、传闻、未跑通的命令）一律标注为"假设"并写明验证方法。

## 提交约定

- 完成一个可验证的工作单元（验收命令跑通即算）就该提交，不攒大批改动；未跑通测试的半成品不提交。
- message 格式沿用 git log 既有风格：`feat|fix|docs|refactor(mN): 一句话结论`。
- **提交与推送前必须经用户确认**；确认后 commit 并 push，保持远程与本地同步。
- 不提交 .gitignore 覆盖的产物（见红线）。

## 常见任务自检（动手前过一眼）

- 改命令 / 目录 / 依赖 → 先同步 AGENTS.md，再动代码，顺序不可反。
- 改设计决策 → 先落 decisions.md 编号条目，再同步设计文档。
- 结束一轮工作 → 回答四问：文档同步了吗？假设补录了吗？红线有违反吗？**改动经确认提交了吗？**

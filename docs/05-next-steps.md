# 05 · 下一步任务清单

> 状态：✅ 当前有效 — M1 已完成，M2（sim 引擎）待启动
> 更新时间：2026-10-16
> 用法：完成一项就在「当前进度」打勾；决策变化必须先改 [decisions.md](decisions.md) 再改这里
> 素人上手顺序：本章 → [decisions.md](decisions.md) → 环境搭建（下节）→ M1

## 0. 当前进度（截至 2026-10-16）

- [x] 前后端分离骨架（FastAPI / React 脚手架，`/api/health` 双端联通）
- [x] 设计文档 00–04 全部定稿，决策 #1–#19 全部落章（无待定阻塞项）
- [x] AGENTS.md 就位（AI 协作规范）
- [x] **M0 R3F 探针**（✅ 已完成，报告见 [05-probe-r3f.md](05-probe-r3f.md)：路线可行，M3 按 5 天排）
- [x] **M1 数据地基**（✅ 已完成 2026-10-16：compose 单 db 服务 + 14 表 ORM（13 业务表 + user） + Alembic 首版迁移（含 vector 扩展） + JWT 双角色；pytest 10/10 绿）
- [ ] **M2 sim 引擎** ← 下一个要做的
- [ ] M3 及以后（见 [04-roadmap.md](04-roadmap.md)）

**MVP 验收动线**（做完 M1–M6 即达成）：
沙盘可看可点 → Agent 1/3 产出真内容 → 人工润色可改 → 扫码可溯源 → 沙盘页内嵌溢价对照图。

**关键约束**：预算约一个月；答辩高光 = Agent 内容生成 + 3D 沙盘流动；
演示必须"断网也能走完闭环"（Agent 产出预生成入库，decisions #11）。

## 1. 环境搭建（所有人开工前一次性做）

前置软件：[uv](https://docs.astral.sh/uv/) ≥ 0.13、Python ≥ 3.13、
Node.js ≥ 20.19、[pnpm](https://pnpm.io/zh/installation) ≥ 10、Docker Desktop。

```bash
# 后端
cd backend
uv sync
cp .env.example .env        # Windows 用 copy；填 OPENAI_API_KEY（可后置）
docker compose up -d        # 仓库根目录执行；先起 PG（M1 后必需）
uv run alembic upgrade head # 建 14 张表（13 业务表 + user）
uv run python -m ruralsmartmark.seed  # 种入演示双账号 operator/coop
uv run pytest               # 应全绿（10 条）
uv run ruralsmartmark       # 起来后 curl http://127.0.0.1:8000/api/health

# 前端（另开一个终端）
cd frontend
pnpm install
pnpm dev                    # 打开 http://localhost:5173 见 3D 探针沙盘
```

M1 已完成，上节命令已含 compose 建库 / 迁移 / seed 三步（compose 文件在仓库根目录）。

## 2. M0 · R3F 探针（✅ 已完成 2026-10-16，结论与踩坑见 [05-probe-r3f.md](05-probe-r3f.md)）

> 结论：路线可行，M3 按 5 天排（原方案 5/10 天二选一，取前者）。
> 版本组合已 pin：`three@0.169` + `@react-three/fiber@8.17`（v8 绑 React 18）+ `@react-three/drei@9.114`。

- [x] `frontend` 安装 `three` `@react-three/fiber` `@react-three/drei`
- [x] Canvas：正交相机 45° 俯视，OrbitControls 旋转缩放
- [x] 场景：程序化生成 4 个站点方块（不同颜色）+ 1 条连线；2 个"小车"小方块沿路径缓动
- [x] 点击方块 → 高亮 + 侧边假数据卡片（硬编码对象即可）
- [x] 60fps 检查：实测 87–122 fps @1280×820，未观察到掉帧
- [x] **产出物**：`docs/05-probe-r3f.md` ——路线可行、耗时不足 1 小时、踩坑与版本 pin 记录、M3 按 5 天排

**验收**：小样能在浏览器跑、可旋转可点击；探针文档写完。
**降级触发条件**（探针结论为可行，此路线仅作 M3 风险备案：若正式场景实体数量/交互密度导致掉帧不可调，改用 2.5D（SVG 等距贴图 + DOM 交互），架构不变，`three/` 目录换成 `iso/`）。

## 3. M1 · 数据地基（✅ 已完成 2026-10-16）

> 依据：decisions #1/#15/#17/#18/#19/#20 + [03-data-model.md](03-data-model.md)（13 张表定稿）

### M1-a docker compose（✅）

- [x] 根目录 `docker-compose.yml`，仅含 `db` 服务：
  - 镜像 `pgvector/pgvector:0.8.7-pg18`（pin 定；官方镜像无 alpine 变体，Debian bookworm 基底）
  - **数据卷：宿主机 `./data/postgres` → 容器 `/var/lib/postgresql`**（decisions #20：本地项目目录绑定卷，上服务器改命名卷；容器内侧是 PG18 新路径，真实 PGDATA 为 `/var/lib/postgresql/18/docker`）
  - `./data/` 加入 .gitignore
  - 环境变量 `POSTGRES_PASSWORD`（本地演示值即可，进 `.env` 不进 git）
  - 健康检查 `pg_isready -U postgres`（✅ 容器 healthy）
- [x] `backend/.env.example` 增加 `DATABASE_URL`（asyncpg 驱动格式）
- [x] `.env.example` 同步：`JWT_SECRET` / `JWT_EXPIRE_HOURS` / `SIM_SEED`（LLM_* 沿用既有 OPENAI_* 配置）

### M1-b ORM 模型 + Alembic（✅）

- [x] `backend` 加依赖 `sqlalchemy[asyncio]` `asyncpg` `alembic`
- [x] `src/ruralsmartmark/db.py`：async engine + sessionmaker（全局单例）
- [x] `src/ruralsmartmark/models/`：14 张表 ORM（13 业务表 + `user`；`product_sku.story_id` 因循环依赖改逻辑外键不加 DB 约束）
- [x] Alembic init + 首版迁移（`migrations/env.py` 接 Settings 与 ORM metadata，asyncpg 异步引擎）
- [x] **迁移里 `CREATE EXTENSION IF NOT EXISTS vector`**（扩展开箱预留，decisions #18）✅ 已验证

### M1-c JWT（✅）

- [x] 依赖 `pyjwt` + 密码哈希（argon2-cffi）
- [x] `POST /api/auth/token`（演示双账号 operator/coop，账号进 seed 不进注册流程）
- [x] FastAPI 依赖注入 `get_current_user` / `require_role("operator")`（+ `/api/auth/me` 验收探针、`/api/sim/control` 假路由验权）
- [x] 测试：无 token 401 / 错角色 403 / 正常 200（tests/test_auth.py 9 条 + health 1 条，全绿）
- [x] seed 脚本：`uv run python -m ruralsmartmark.seed`（幂等）

### M1 验收清单（✅ 全部通过 2026-10-16）

```bash
docker compose up -d                          # db healthy
cd backend && uv run alembic upgrade head     # 15 张表建成（14 + alembic_version）
uv run alembic downgrade base && uv run alembic upgrade head  # 可重放 ✅
uv run pytest                                 # 10 passed ✅
```

## 4. 再往后（简报，细则到点再写）

2. **M2 · sim 引擎**：虚拟时钟 tick = 1 模拟分钟（可暂停/变速/重置，REST 控制），
   六类实体状态机，可重放固定剧本（seed 可选），变更落库 + WS 增量广播；
   快照接口 `/api/world/snapshot` 读现势表
3. **M3 · 3D 沙盘**：R3F 正式场景吃 WS 数据；探针的 `three/` 代码迁进来正式化
4. **M4 · Agent 1/3**：`agents/llm.py` OpenAI 兼容封装（智谱/DeepSeek 可切换），
   故事/文案两个 Agent + 工作台润色闭环（artifact 三态：draft→polished→final）
5. **M5 · 溯源 H5**：`/t/:code` 公开页，时间线读 `trace_event`，文案复用 Agent 1 定稿
6. **M6 · 溢价**：price_benchmark 落数 + 沙盘页内嵌对照图
7. **M7 · 冲刺**：独立看板 / Agent 2 / Agent 5 / 温度曲线 / 答辩剧本 / 演示视频

分工建议（4 人以上时）：3D 线（M3）/ 后端线（M1+M2）/ Agent 线（M4）/
溯源+溢价线（M5+M6）可并行，M1/M2 完成前 3D 线用 M0 探针的假数据先行。

## 5. 未验证假设（开工即验证）

- [ ] Docker Desktop 在目标演示机可用且内存充足（PG 起得来）
- [ ] OPENAI 兼容端点（智谱/DeepSeek 任一）key 可用，中文故事质量达标（M4 前置检查）
- [ ] SiliconFlow 生图网关可注册、模型可用；定价/限流与账号额度、水印关闭（X-Enable-Watermark: 0）在后台核验（Agent 2 启动前置检查，decisions #13）
- [ ] uv / pnpm 在团队各机器安装无障碍

## 6. 红线复查（开工前最后过一眼）

不引 LangChain / Celery / Redis / 向量库；PG 数据卷路径 `/var/lib/postgresql`；
`.env` 不入库；`dist/` 不入库不手改；界面文案中文；docs 与 decisions.md 冲突时
以 decisions.md 最新条目为准。

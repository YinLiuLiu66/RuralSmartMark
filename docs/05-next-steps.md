# 05 · 下一步任务清单

> 状态：✅ 当前有效 — M1 未动工，本文件是唯一在执行的作业指导
> 更新时间：2026-10-15
> 用法：完成一项就在「当前进度」打勾；决策变化必须先改 [decisions.md](decisions.md) 再改这里
> 素人上手顺序：本章 → [decisions.md](decisions.md) → 环境搭建（下节）→ M1

## 0. 当前进度（截至 2026-10-15）

- [x] 前后端分离骨架（FastAPI / React 脚手架，`/api/health` 双端联通）
- [x] 设计文档 00–04 全部定稿，决策 #1–#19 全部落章（无待定阻塞项）
- [x] AGENTS.md 就位（AI 协作规范）
- [ ] **M0 R3F 探针** ← 下一个要做的
- [ ] M1 数据地基
- [ ] M2 及以后（见 [04-roadmap.md](04-roadmap.md)，不在本文档展开）

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
uv run pytest               # 应全绿（当前仅 1 条 health 测试）
uv run ruralsmartmark       # 起来后 curl http://127.0.0.1:8000/api/health

# 前端（另开一个终端）
cd frontend
pnpm install
pnpm dev                    # 打开 http://localhost:5173 见占位页
```

M1 完成后此处需补：`docker compose up -d` 先起库，再执行后端命令（届时更新本节与 AGENTS.md）。

## 2. M0 · R3F 探针（先行，约 1 天）

> 目的：验证"程序化 low-poly 等距沙盘"这条 3D 路线的真实成本，产出量级感
> 决策依据：decisions #16（M3 依赖本探针结论），decisions #3（纯几何体拼装）

- [ ] `frontend` 安装 `three` `@react-three/fiber` `@react-three/drei`（探针专用分支或临时提交均可）
- [ ] Canvas：正交相机 45° 俯视，OrbitControls 旋转缩放
- [ ] 场景：程序化生成 4 个站点方块（不同颜色）+ 1 条连线；2 个"小车"小方块沿路径缓动
- [ ] 点击方块 → 高亮 + 侧边假数据卡片（硬编码对象即可）
- [ ] 60fps 检查（React DevTools Profiler 或肉眼），记录掉帧场景
- [ ] **产出物**：`docs/05-probe-r3f.md` —— 结论：路线可行/不可行、实现耗时、踩坑记录、M3 预估天数

**验收**：小样能在浏览器跑、可旋转可点击；探针文档写完。
**不可行时的降级路线**（探针文档里写明触发条件）：改用 2.5D（SVG 等距贴图 + DOM 交互），架构不变，`three/` 目录换成 `iso/`。

## 3. M1 · 数据地基（M0 通过后启动）

> 依据：decisions #1/#15/#17/#18/#19 + [03-data-model.md](03-data-model.md)（13 张表定稿）

### M1-a docker compose

- [ ] 根目录 `docker-compose.yml`，仅含 `db` 服务：
  - 镜像 `pgvector/pgvector:pg18`（tag 落笔当天查 Docker Hub pin 最新补丁号）
  - **数据卷挂 `/var/lib/postgresql`**（PG18 不再带 `/data` 后缀，挂错库不落盘）
  - 环境变量 `POSTGRES_PASSWORD`（本地演示值即可，进 `.env` 不进 git）
  - 健康检查 `pg_isready -U postgres`
- [ ] `backend/.env.example` 增加 `DATABASE_URL`（asyncpg 驱动格式）
- [ ] `.env.example` 同步：`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` / `JWT_SECRET` / `SIM_SEED`

### M1-b ORM 模型 + Alembic

- [ ] `backend` 加依赖 `sqlalchemy[asyncio]` `asyncpg` `alembic`
- [ ] `src/ruralsmartmark/db.py`：async engine + sessionmaker（全局单例）
- [ ] `src/ruralsmartmark/models/`：13 张表 ORM（对照 03 文档逐表核对字段）
- [ ] Alembic init + 首版迁移：`alembic init migrations` → 生成并检查首版脚本
- [ ] **迁移里 `CREATE EXTENSION IF NOT EXISTS vector`**（扩展开箱预留，decisions #18）

### M1-c JWT

- [ ] 依赖 `pyjwt` + 密码哈希（`passlib[bcrypt]` 或 argon2）
- [ ] `POST /api/auth/token`（演示双账号运营方/合作社，账号进 seed 不进注册流程）
- [ ] FastAPI 依赖注入 `get_current_user` / `require_role("operator")` 等
- [ ] 测试：无 token 401 / 错角色 403 / 正常 200（sim control 用假路由验权）

### M1 验收清单

```bash
docker compose up -d                          # db 健康
cd backend && uv run alembic upgrade head     # 13 张表建成
uv run alembic downgrade base && uv run alembic upgrade head  # 可重放
uv run pytest                                 # 全绿，含新 auth 测试
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

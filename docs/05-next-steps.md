# 05 · 下一步任务清单

> 状态：🟢 M6 已完成（2026-10-21 浏览器验收通过），下一步 M7
> 更新时间：2026-10-21
> 用法：完成一项就在「当前进度」打勾；决策变化必须先改 [decisions.md](decisions.md) 再改这里
> 素人上手顺序：本章 → [decisions.md](decisions.md) → 环境搭建（下节）→ M1

## 0. 当前进度（截至 2026-10-21）

- [x] 前后端分离骨架（FastAPI / React 脚手架，`/api/health` 双端联通）
- [x] 设计文档 00–04 全部定稿，决策 #1–#29 全部落章（无待定阻塞项）
- [x] AGENTS.md 就位（AI 协作规范）
- [x] **M0 R3F 探针**（✅ 已完成，报告见 [05-probe-r3f.md](05-probe-r3f.md)：路线可行，M3 按 5 天排）
- [x] **M1 数据地基**（✅ 已完成 2026-10-16：compose 单 db 服务 + 14 表 ORM（13 业务表 + user） + Alembic 首版迁移（含 vector 扩展） + JWT 双角色；pytest 10/10 绿）
- [x] **M2 sim 引擎**（✅ 已完成 2026-10-16：虚拟时钟 + 剧本双写 + 控制/快照/WS，任务细则见 §4）
- [x] **M3 3D 沙盘**（✅ 已完成 2026-10-16：快照+WS 数据链路 / 场景正式化 / 钟控条，细则见 §5）
- [x] **M4 Agent 1/3**（✅ 已完成 2026-10-21：Agent 1/3 + 独立工作台 + 麻江真实县域；浏览器动线验收通过；#24–#29，细则见 §6）
- [x] **M5 溯源 H5**（✅ 已完成 2026-10-21：固定演示码 MJDEMO22 + 17 节点预置时间线 + 公开 `/api/trace/{code}` + `/t/:code` H5 + 工作台二维码；#30，细则见 §7）
- [x] **M6 溢价对照**（✅ 已完成 2026-10-21：三档演示测算 + 公开 `/api/pricing/benchmarks` + 沙盘右下可折叠纯 CSS 图；#31，细则见 §8）
- [ ] M7 及以后（见 §9）

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
- [x] `.env.example` 同步：`JWT_SECRET` / `JWT_EXPIRE_HOURS` / `SIM_SEED`（LLM 配置沿用既有 `OPENAI_*`，见 decisions #21）

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

## 4. M2 · sim 引擎（✅ 已完成 2026-10-16，"世界活了"）

> 依据：decisions #5（可重放剧本）/ #11（预生成入库）/ #15（现势实体表 + 历史事件流水）/
> #17（REST 控制与快照主从）/ #19（WS 不区分角色）
> 三条铁律：① 模拟时间与真实时间分离——业务时间戳（trace/telemetry/运单时点）一律写模拟时间；
> ② 先落库成功再广播——WS 事件只在 commit 之后发；③ reset 必须回到剧本起点——演示可无限次完整重放。

### M2-a 引擎内核（时钟 + 事件总线 + 主循环）✅

- [x] `sim/clock.py`：虚拟时钟——1 tick = 1 模拟分钟，sim_time 从演示日 07:00 起
      （Asia/Shanghai 时区感知），running / speed 字段（限速 1–10×，tick 间隔 = 2s / speed）
- [x] `ws/bus.py`：WebSocket 连接管理器 + 事件总线（事件封套 `{type, sim_time, data}`，
      全体广播不区分角色）
- [x] `sim/engine.py`：SimEngine——lifespan 托管 asyncio 主循环：每 tick 推进剧本 → 落库 → 广播；
      **启动即 reset 重建世界**（后端重启 = 演示起点，不依赖从 DB 复原内存态）；
      单 tick 失败记日志不致死循环；reset 保留当前倍速

### M2-b 剧本状态机 + trace_event 双写 ✅

- [x] `sim/state_machines.py`：运单五步 confirmed→picked→loaded→in_transit→delivered
      与 shipment_next() 助手；车辆四态 / worker 枚举与 runtime 模型注释同源
- [x] `sim/scenario.py`：初始世界（1 合作社 + 4 站点【复用 M0 探针坐标】+ 2 车 + 5 工人
      + 2 SKU + 集货仓预置 4 托）+ 剧本链路：
      一程 农场→集货仓（时间驱动，100 分钟周期：采摘 t=0 → 分装 t=12 → 预冷入库 t=22
      → 运单确认 t=30 → 装车 t=36 → 发车 t=42 → 到站 t=68 → 卸货 t=74 → 送达 t=76 → 空驶返场）；
      二程/三程 集货仓→前置仓→门店（事件驱动：存量 ≥4 触发，同车越库转 B 单直发）
- [x] **双写规则**：每次状态转移 = 实体表现势回写 + `trace_event` 追加一行
      （模拟时间存 payload.sim_ts；append-only）
- [x] `telemetry` 流水：在途车每 tick 一行（固定 seed 高斯抖动）；载货在途时按 3%/tick
      概率触发 temp_alert（固定 seed 下确定；实测约一程 2–3 次，画面有剧情）
- [x] 固定 seed：`SIM_SEED=7` → random.Random；reset 清空运行时表回剧本起点
      （product_sku / user / agent_* 不清，cooperative 及其下全量重建）

### M2-c 控制 + 快照 + WS 路由 ✅

- [x] `routes/sim.py`：POST /api/sim/control（pause/resume/speed/reset，speed 1–10 校验 422，
      限 operator）；控制动作广播 tick.info，reset 广播 world.reset
- [x] `routes/world.py`：GET /api/world/snapshot（时钟 + 四类实体现势 + 未送达与最近 10 笔
      已送达运单 + 在途路线，公开读）+ WS /ws/world（增量流，不鉴权，decisions #19）
- [x] `app.py`：撤 M1 假路由；lifespan 拉起/停止引擎（TestClient 不进 lifespan，测试零干扰）
- [x] 事件集：`tick.info` / `entity.updated`（vehicle/worker/pallet）/ `shipment.progressed`
      / `world.reset`；`agent.*` / `scheduler.*` 留给 M4

### M2 验收清单（✅ 全部通过 2026-10-16）

```bash
cd backend && uv run ruff check . && uv run pytest   # ruff 零告警；15 passed（M1 10 + M2 5）✅
uv run ruralsmartmark                                # 起服务世界自动运转 ✅
# curl /api/world/snapshot：时钟在走、truck2 在途带 route、运单逐步推进 ✅
# 控制三连：speed=8 → 6 秒推 23 tick（理论 ~24）；pause → 3 秒 0 tick ✅
# WS 10 秒实收：tick.info ×10 / entity.updated ×12 / shipment.progressed ×2 ✅
# DB 复核：trace_event 双写按节点累积（loaded/departed 12、temp_alert 8）；
#          telemetry 72 行全为模拟时间（07:10→08:12，非墙上时钟）✅
```

**M2 施工记录**：剧本计划队列的 partial 一律传关键字参数（位置参数会前插到 session 之前）；
跨 tick 只持主键不持 ORM 实例（每 tick 独立 session）。

## 5. M3 · 3D 沙盘（✅ 已完成 2026-10-16，"看得见"）

> 依据：M0 探针结论（[05-probe-r3f.md](05-probe-r3f.md)：版本 pin 组合 + 正交相机 near=-80 +
> drei Line + e.delta>6 防误触）+ decisions #8（Zustand 管沙盘实时态）；
> 数据源 = M2 `GET /api/world/snapshot`（初始化）+ `/ws/world` 增量（实时）。

### M3-a 数据链路（类型 + client + 状态库）✅

- [x] `api/types.ts`：WorldSnapshot / 事件封套 `{type, sim_time, data}` 类型（与 03 §3.1 对齐）
- [x] `api/client.ts` 加 `fetchWorldSnapshot()` / `simControl()`；新增 `api/ws.ts`：
      WS 连接（相对 URL 自动推导协议与 host，兼容代理与同源部署）+ 指数退避自动重连
- [x] `stores/world.ts`：Zustand——快照全量 + WS 增量合并（entity.updated 按 entity+id
      upsert；shipment.progressed 并入运单列表；tick.info 驱动实时钟；`world.reset` 重拉快照）

### M3-b 场景正式化（探针 → 正式沙盘）✅

- [x] `three/WorldScene.tsx`：沿用探针的相机/灯光/网格/OrbitControls；站点吃
      stores 快照（`pos_x/pos_z`），托盘量映射站点方块高度；站点/车辆皆可点选
- [x] `three/VehicleMesh.tsx`：在途车辆读快照 `route`（起止站坐标 + departed/arrives），
      按 `tick.info.sim_time` 起讫直线插值（正交 45° 俯视下与公路弧线偏差可忽略，探针实测）；
      到站车停靠站点旁固定位置；车辆按 id 区分色标
- [x] 详情卡 `three/DetailCard.tsx`：站点卡（名称/类型/库存/批次列表）/ 车辆卡（状态/温湿度/
      路线起止 + 当前-active 运单五步 stepper）/ 运单卡——复用探针玻璃拟态卡样式
- [x] `probeData.ts` 假数据退役：探针三件套（ProbeScene/FpsBadge 沿用/probeData 删），
      站点配色改按站点序（探针四色：绿/橙/蓝/紫）

### M3-c 沙盘控制条（decisions #17 控制入口演示位）✅

- [x] 顶部时钟条 `panels/ClockBar.tsx`：`sim_time` + 速度 + 运行态（tick.info 驱动）
- [x] operator 已登录则显示 暂停/继续/变速（1/2/4/8×）/重置 按钮（`POST /api/sim/control`，
      JWT 存 localStorage `rsm_jwt`；未登录隐藏按钮不显示登录表单——M4 工作台再补登录 UI）
- [x] `world.reset`/重置按钮反馈：快照重拉 + 卡片关闭（reset 由 store 统一处理）

### M3 验收（✅ 全部通过 2026-10-16）

```bash
cd frontend && pnpm typecheck && pnpm lint && pnpm build
# tsc 零错误 / oxlint 0 warnings 0 errors / vite build ✓（996KB 大包警告为探针已知项，收尾期拆包）
uv run ruralsmartmark && pnpm dev                            # 双端起来
# 浏览器实测（GUI 黑盒，1280×860）：
# 站点真实数据卡（名称/类型/在库托盘/批次）✅；帧率 120–121 fps 无掉帧 ✅
# 时钟实时推进（5 真实秒 = 5 模拟分钟 @2×）✅
# 8× 变速 5 秒推 17 分钟、暂停钟面冻结、重置回 07:00 ✅
# 在途车沿路移动、停靠位置固定可点 ✅；车辆卡含温湿度/路线/运单 stepper ✅
```

**M3 施工记录（踩坑）**：vite 开发代理必须显式配 `/ws` 条目（`ws: true` +
`target: ws://127.0.0.1:8000`），否则 WS 走不通表现为"时钟冻结、快照正常"；
WS 客户端 URL 用 `new URL(path, location.href)` 相对推导，勿手拼 host（代理链路下会构造出坏路径）。

## 6. M4 · Agent 1/3（✅ 已完成 2026-10-21）

> 依据：decisions #23（模型）/ #24（独立工作台）/ #25（operator 全权）/ #26（REST+WS，不做 SSE）/
> #27（固定素材 + DB 事实注入）/ #28（真实县域：贵州麻江县·蓝莓）/ #29（文案事实边界）
> 验收动线：登录 operator → 工作台发起故事任务 → 生成中 → 产出 draft → 编辑 → polished → final；
> 断网时命中预生成入库内容（#11）。

### M4-a LLM 封装 + 素材包
- [x] `agents/llm.py`：AsyncOpenAI 封装（读 `OPENAI_*`；空 key 走 mock，测试不联网；超时/错误映射）
- [x] `agents/materials/majiang.json`：麻江县·蓝莓的产业事实（附出处）+ 农户口述 + 苗族传说
- [x] `agents/context.py`：从 DB 取合作社/站点/冷链温度/运输时长，拼 3–5 个事实进 Prompt
- [x] `agents/prompts.py`：故事（Agent 1）/ 文案（Agent 3）Prompt 集中管理

### M4-b 任务 API + 后台执行
- [x] `schemas/agents.py`：任务/产出物的请求响应模型
- [x] `routes/agents.py`：`POST /api/agent-tasks`、`GET /api/agent-tasks`、`PATCH /api/agent-artifacts/{id}`
- [x] 后台任务：pending→running→done/failed；先落库再广播 `agent.task_updated` / `agent.artifact_ready`
- [x] 权限：operator 全权；coop 可发起、只能改自己草稿（#25）

### M4-c 工作台（独立页面）
- [x] 引入 `react-router-dom` + TanStack Query（#8/#24）；`/` 沙盘、`/workbench` 工作台、顶部导航
- [x] 登录弹窗（演示双账号 operator/coop，JWT 存 `rsm_jwt`）
- [x] 任务列表 / 发起任务 / 产出物编辑 / draft→polished→final 流转
- [x] WS 事件只做 TQ 缓存失效（#26）

### M4-d 预生成与验收
- [x] 真实模型生成故事 + 文案并落库（`python -m ruralsmartmark.agents.pregenerate`，断网兜底 #11）
- [x] `pytest` 23 passed / `ruff check` 零告警 / `pnpm typecheck` `lint` `build` 通过
- [x] 浏览器实测完整动线（2026-10-21：未登录 → operator 登录 → 生成中 → 初稿 → 编辑保存 → 润色 → 定稿；coop 登录 → 只读他人草稿、仅能保存自己草稿；失败态徽章与文案；沙盘导航切换）

**M4 施工记录**：任务执行用 FastAPI `BackgroundTasks`（TestClient 会等后台跑完，测试可直接断言终态；
真实请求先返回 pending，再由 WS 推 done）；故事实测约 21 秒/475 字、文案 545 字，均含 DB 注入的冷链温度与站点；
前端新增依赖 `react-router-dom@6.30` + `@tanstack/react-query@5`；`/workbench` 由 Vite history fallback 承载。
**2026-10-21 验收修复**：① 沙盘 `.app-shell` 改 `padding-top` 抵消导航高度，消除 56px 文档溢出导致的标题/时钟被遮挡；
② 合作社查看他人草稿改为只读（前端按 `created_by` 判定，后端 403 仍兜底）；③ 401 自动登出并提示"登录已过期"；
④ 生成提示改为约 20 秒；⑤ 按 #29 收紧 Prompt 并重生成定稿（故事 #6 482 字、文案 #7 479 字），旧定稿降为 draft 保留历史。

## 7. M5 · 溯源 H5（✅ 已完成 2026-10-21）

> 依据：decisions #9（图文时间线）/ #15（trace_event 源）/ #16（MVP 闭环）/ #30（固定演示码 + 预置时间线）
> 验收动线：工作台打开“溯源二维码” → 手机/浏览器打开 `/t/MJDEMO22` → 产品 + Agent 1 定稿故事 + 17 节点时间线（含温控告警与门店签收）→ 未知码 404。

### M5-a 演示数据
- [x] 固定演示码 `MJDEMO22`（批次 `MJ-DEMO-001`）；`build_initial_world` 每次 reset 重建，码/URL 不变
- [x] 预置 17 节点完整时间线：采摘 → 分拣包装 → 预冷 → 装车 → 发车 → 温控告警 → 集货仓 → 前置仓 → 门店 → 签收
- [x] 最终一程门店送达补 `delivered` 流水；集货仓/前置仓到站只记 `unloaded`
- [x] 演示托盘停在门店，不参与二程/三程取货；M2 计数测试已排除演示托盘

### M5-b 公开接口
- [x] `GET /api/trace/{code}`（无需鉴权）；码大小写归一；未知码 404
- [x] 响应：产品/批次/数量/定价 + 最新 final 品牌故事 + 时间线（站点/车辆/备注/温度）
- [x] `tests/test_trace.py` 2 条 + `test_sim.py` 最终签收 1 条；pytest 26 passed

### M5-c H5 页面
- [x] `/t/:code` 独立路由，隐藏顶部导航；移动优先暗色版式
- [x] 产品卡 / Agent 1 定稿故事（IP 定位高亮）/ 17 节点竖向时间线 / 404 状态
- [x] 工作台 operator 增加“溯源二维码”按钮：QR 跟随当前 origin + 链接 + localhost 提示
- [x] 390×844 手机视口：无横向溢出，告警/签收节点清晰

**M5 验收记录**：`curl /api/trace/MJDEMO22` 返回 17 节点与故事 #6；`curl /api/trace/NOTACODE` 返回 404；pytest 26 passed；ruff 零告警；`pnpm typecheck` / `lint` / `build` 通过；浏览器桌面 + 390px 手机实测。
**手机扫码注意**：二维码编码当前 origin。用 `pnpm dev --host` 启动，并在电脑浏览器用局域网地址打开工作台；本机 localhost 的二维码手机扫不到（弹窗已提示）。

## 8. M6 · 溢价对照（✅ 已完成 2026-10-21）

> 依据：decisions #16（MVP 闭环收尾）/ #31（演示测算 + 轻量 CSS 图）
> 验收动线：沙盘右下“溢价对照” → 展开三档散装行情与礼盒价 → 溢价率 + 演示测算说明。

### M6-a 数据与接口
- [x] `price_benchmark` 三档演示测算：批发市场 ¥36 / 电商散装 ¥58 / 礼盒直营 ¥72，礼盒价 ¥128；溢价率按 `(128-bulk)/bulk` 计算
- [x] `build_initial_world` 幂等 upsert（reset 不重复、不清空 `price_benchmark`）
- [x] `GET /api/pricing/benchmarks` 公开读；响应含 sku/items/note
- [x] `tests/test_pricing.py` 2 条；pytest 28 passed

### M6-b 沙盘对照卡
- [x] 右下角可折叠卡：收起态 190px 小胶囊，展开态 300px 纯 CSS 条形图
- [x] 三档渠道、散装/礼盒双条、溢价率、演示测算说明
- [x] 不引 ECharts（留给 M7 独立看板）；无新增图表依赖
- [x] 浏览器桌面实测收起/展开，120fps 未受影响

**M6 验收记录**：`curl /api/pricing/benchmarks` 返回三档；pytest 28 passed；ruff 零告警；tsc/oxlint/vite build 通过；沙盘卡展开/收起与数值实测。
**口径提醒**：散装价为演示值，页面已标注“演示测算”；真实行情未采集（见 §10）。

## 9. 再往后（M7 简报，细则到点再写）

1. **M7 · 冲刺**：独立看板（ECharts）/ Agent 2 / Agent 5 / 温度曲线 / 答辩剧本 / 演示视频
2. **M7 可选**：Agent 4 的“把溢价结论说成人话”（M6 只做数字与图）

分工建议（4 人以上时）：3D 线（M3）/ 后端线（M1+M2）/ Agent 线（M4）/
溯源+溢价线（M5+M6）可并行，M1/M2 完成前 3D 线用 M0 探针的假数据先行。

## 10. 未验证假设（开工即验证）

- [ ] Docker Desktop 在目标演示机可用且内存充足（PG 起得来）
- [x] OpenAI 兼容端点与 key 可用（2026-10-20 实测 SiliconFlow：`/v1/models` 200 且含目标 id，`/v1/chat/completions` 200 返回中文）
- [x] 中文故事/文案质量达标（2026-10-20 实测：故事 475 字/21.7 秒、文案 545 字，含真实冷链温度与站点；见 #23）
- [x] 长文案（300–500 字）耗时实测约 20–22 秒（2026-10-21 浏览器动线：任务 #4/#5，含生成中态）
- [ ] 手机真机扫码（需 `pnpm dev --host` + 局域网地址；M5 弹窗已提示 localhost 限制，尚未真机验证）
- [ ] 真实蓝莓行情价未采集；M6 用演示测算并已标注（decisions #31）。若答辩要引用真实价格，需另行核价。
- [ ] SiliconFlow 生图网关可注册、模型可用；定价/限流与账号额度、水印关闭（X-Enable-Watermark: 0）在后台核验（Agent 2 启动前置检查，decisions #13）
- [ ] uv / pnpm 在团队各机器安装无障碍

## 11. 红线复查（开工前最后过一眼）

不引 LangChain / Celery / Redis / 向量库；PG 数据卷路径 `/var/lib/postgresql`；
`.env` 不入库；`dist/` 不入库不手改；界面文案中文；docs 与 decisions.md 冲突时
以 decisions.md 最新条目为准。

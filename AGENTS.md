# AGENTS.md


## 项目定位

- 「挑战杯」v2：县域农产品（首个案例昭通丑苹果）的 AI 品牌流水线 + 3D 沙盘 + 溯源 H5。
- 四个 Agent：故事/IP、包装设计、内容营销、定价/溯源；一个批次从田间走到消费者。
- 优先级：端到端闭环 > 视觉/交互 > 代码整洁 > 生产运维（并发/真实数据）。
- 面向人的界面与文案一律中文；代码注释不写“怎么调/做什么”类废话。
- 架构取舍先落 `docs/decisions.md`（v2 从 #32 起）；冲突以最新条目为准。

## 当前阶段（2026-10-21）

- **Phase 0 已完成**：`rewrite/v2` 分支；旧 v1 后端/前端/文档/Postgres 数据已移出工作树（`main` 保留历史）；SQLite 9 张表 + Alembic 初始迁移；seed；Mock LLM/Image Provider；`/api/health`、`/api/products`、`/api/batches`、`/api/demo/reset`；前端 React 19 + R3F 9 + Tailwind 4 骨架、3D 场景、`/trace` 骨架。
- **Phase 1 已完成**：mock 四 Agent 流水线（story→packaging→marketing→pricing）、`AgentRun`/`Artifact`/workspace、人工审核/驳回/重跑、SSE、站点卡、批次沿站点移动、审核后自动启动下一站。
- **Phase 2 已完成**：真实 LLM Agent（结构化输出 + 失败重试 + mock 兜底）、10 篇知识库 Markdown、FactGuard（逐字引用/违禁词/数字预警）、确定性定价计算器、包装 SVG 预览 + Pillow PNG、引用/预警/包装预览 UI、知识库 API。
- **下一步 Phase 3**：沙盘联动（包装贴图/广告牌/二维码）+ 公开溯源 API/H5 + IP 对话。
- **尚未实现**：公开溯源 API/IP 对话、3D 包装贴图、真实图像 Provider、字段级审核表单（当前 JSON 编辑器）、扫码统计落库。别假设它们存在。

## 环境特殊性（缺就是缺，别假设有）

- 包管理器：uv（后端）+ pnpm（前端）；不存在 requirements.txt / package-lock。
  已实测：Python 3.13、uv 0.13、Node 24、pnpm 12。
- 数据库：**SQLite**，默认 `backend/data/app.db`（已 gitignore）；不需要 Docker/Postgres。
- `.env`：`backend/.env.example` 复制为 `.env`；`OPENAI_API_KEY` 可空，空则走 Mock；
  `DATABASE_URL` 默认 `sqlite+aiosqlite:///./data/app.db`；`AUTO_APPROVE` 默认 false；
  `LLM_FALLBACK_TO_MOCK=true`、`LLM_TIMEOUT_SECONDS=180`（营销长文实测需要更长超时）；`LLM_THINKING_BUDGET=2048`（128–32768，0 关闭）、`LLM_MAX_TOKENS=4096`。默认模型 `deepseek-ai/DeepSeek-V4.1-Flash`。
- 知识库 `data/knowledge/zhaotong/*.md` 是事实真源（已入库）；seed 时 upsert 到 `knowledge_doc`。
  运行期包装 PNG 在 `backend/data/artifacts/`（gitignore）。
- `uv run pytest` **不需要 PG**；测试用临时 SQLite；单函数一样跑。
- 前端没有测试框架；只有 `pnpm typecheck` / `pnpm lint` / `pnpm build` 兜底；别假设有 vitest/jest。
- 3D 只在桌面端（≥1024px）；手机只走 `/trace/:code`。3D 构建方式对齐 WareTrack：
  代码拼 Box/Cylinder/Cone/Sphere/Plane + MeshStandardMaterial + CanvasTexture；不引 GLB/写实资产。
- 固定演示批次 `ZT-DEMO-001` / 溯源码 `ZTDEMO26`；seed 幂等；`POST /api/demo/reset` 重建批次。
- 前端 Vite 代理 `/api` → `http://127.0.0.1:8000`。

## 技能包同步（每个 Agent 开工必做）

- `.agent/skills/` 是仓库内技能唯一真源：`agents-md-craft` / `frontend-craft` / `liu-meta-skill`。
- 开工时只把当前任务需要的技能同步到自己的发现目录：
  - ZCode：`~/.zcode/skills/`（或项目级 `.zcode/skills/`，以实际加载路径为准）
  - Claude Code：`.claude/skills/`
  - 其他工具：按该工具文档。
- 方向单向：`.agent/skills/` → 工具目录；目标已有同名技能以仓库源为准。
- 工具私有目录（`.claude/`、`.zcode/`）不入库；`.agent/skills/` 才是团队共享源。

## 常用命令

后端（在 `backend/`）：

- `uv sync` → 依赖安装（别手动建 venv）
- `uv run alembic upgrade head` → 建表/迁移
- `uv run python -m ruralsmartmark.seed` → 种演示数据（幂等）
- `uv run ruralsmartmark` → 起服务，端口 8000
- `uv run pytest` → 全测试；单函数：`uv run pytest tests/test_health.py::test_health`
- `uv run ruff check .` → 静态检查；`uv run ruff format .` → 格式化

前端（在 `frontend/`）：

- `pnpm install` → 依赖
- `pnpm dev` → 开发服，端口 5173
- `pnpm typecheck` / `pnpm lint` / `pnpm build`

文档无构建步骤，直接改 `.md`。

## 目录地图（改哪去哪，产物别碰）

```
backend/
  src/ruralsmartmark/
    main.py config.py db.py deps.py models.py schemas.py
    routes/ health.py products.py batches.py demo.py pipeline.py
           knowledge.py artifacts.py        # 知识库清单 + 包装文件下载
    agents/ base.py schemas.py prompts.py engine.py runtime.py mock.py orchestrator.py
    providers/ llm.py image.py      # Provider 接口 + Mock
    services/ events.py workspace.py knowledge.py fact_guard.py pricing.py packaging.py
    seed/ __init__.py __main__.py   # 幂等 seed（含知识库 Markdown）
  migrations/                       # Alembic 生成物，ruff 不检
  alembic.ini pyproject.toml
  tests/ conftest.py test_health.py test_seed.py test_batches.py test_pipeline.py
         test_knowledge.py test_fact_guard.py test_pricing.py test_engine.py
data/knowledge/zhaotong/*.md        # 事实源；已入库
frontend/
  src/api/client.ts                 # fetch 封装 + Product/Batch/Knowledge 类型
  src/api/pipeline.ts               # workspace/run/approve/reject + guard 类型
  src/agents.ts                     # Agent 元数据、状态映射、下一站/审核站
  src/stores/world.ts               # Zustand：批次/选中批次
  src/stores/pipeline.ts            # Zustand：workspace/选中 Agent/busy
  src/three/Scene.tsx               # 等距正交场景（果园/四站点/批次移动/站点状态）
  src/three/stations.ts             # 四站点元数据
  src/components/StationCard.tsx    # 工位卡（预览/引用/FactGuard/包装图）
  src/components/ReviewDialog.tsx   # 原生 dialog 审核（JSON + 引用/预警/包装预览）
  src/routes/Sandbox.tsx            # 桌面沙盘 `/` + SSE + 审核动线
  src/routes/Trace.tsx              # 移动溯源骨架 `/trace/:code`（Phase 3 接 API）
  src/styles/global.css             # Tailwind v4 @theme + 山野编辑部 token
  vite.config.ts package.json
docs/
  decisions.md                      # v2 #32 起；唯一决策真源（v1 已移除）
  v2/plan.md                        # v2 产品/架构方案
  v2/ui.md                          # 前端六行契约/token/组件/七类丑
  v2/sources.md                     # 昭通事实待核验清单
  05-next-steps.md                  # 唯一动态任务清单
.agent/skills/                      # 可复用技能包
```

尚未创建、创建前勿假设存在：公开溯源 API/IP 对话、3D 包装贴图、真实图像 Provider、扫码统计写入、字段级审核表单。
子目录若有专属强约定，另建 `<dir>/AGENTS.md`，根文件只引用不复制。

## 文档维护职责（必读必做）

核心原则：文档与代码一旦产生偏差，要么立刻修文档，要么立刻报告差异，不许含糊带过。
每条事实只允许在一处权威定义，其他位置一律引用路径，禁止复制正文。

| 文档 | 权威范围 | Agent 必做的维护 |
| --- | --- | --- |
| AGENTS.md | 操作事实：命令 / 环境 / 目录 / 红线 | 改动命令、目录、依赖、端口、env、测试方式后必须同步；过时行直接删 |
| docs/decisions.md | 决策权威：唯一真源 | 任何拍板先新增 #N 条目；v2 从 #32 起；不重排已有 v2 编号 |
| docs/v2/plan.md | v2 产品/架构方案 | 方案变化先改 decisions，再同步本文 |
| docs/v2/ui.md | 前端设计契约 / token / 组件 | 前端结构、token、组件变化时同步 |
| docs/v2/sources.md | 昭通事实待核验清单 | 每条事实补 source_url / 原文 / 日期；冲突用区间 |
| docs/05-next-steps.md | 唯一动态任务清单 | 开工前写条目与假设；完工打勾；新假设补录 |
| README.md | 人类读者入口 | 运行方式/目录变化时同步；不复制 AGENTS 的约束 |

v1 设计文档已移除；如需追溯见 git history（main 分支）。与 v2 冲突时以 `docs/v2/` 与 `decisions.md` 为准。

## 红线

- 不做游戏化任务/评分、多产品 UI、登录/权限、真实电商 API、Canva/Midjourney 直连、IoT 温度曲线。
- 不做写实 3D/自定义 GLB 管线；不做移动端 3D 沙盘。
- 不引 LangChain / LlamaIndex / Celery / Redis / Chroma；不引向量数据库。
- 不提交 `.env`、`backend/data/`、`node_modules/`、`dist/`、`.zcode/` 等被 ignore 的产物；改 .gitignore 需理由。
- 昭通事实必须有 `source_url` + 检索日期；演示数字标“演示测算”；不编真实人物/认证/功效。
- 不把 v1 代码、旧 CSS token、旧 Postgres/Docker 约定重新引入；旧代码只在 git history / 旧 docs 历史里。
- 无法核实的事实（假设、传闻、未跑通的命令）一律标注“假设”并写明验证方法。

## 提交约定

- 完成一个可验证的工作单元即可提交；但 **commit/push 前先向用户确认**（用户习惯，优先于旧约定）。
- message 格式：`feat|fix|docs|refactor(mN): 一句话结论`。
- 未跑通测试的半成品不提交；不提交 .gitignore 覆盖的产物。

## 常见任务自检（动手前过一眼）

- 改命令/目录/依赖 → 先同步 AGENTS.md，再动代码。
- 改架构决策 → 先落 docs/decisions.md #N，再同步 docs/v2/。
- 结束一轮 → 文档同步了吗？假设补录了吗？红线有违反吗？改动经确认提交了吗？

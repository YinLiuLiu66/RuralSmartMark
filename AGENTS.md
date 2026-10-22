# AGENTS.md


## 项目定位

- 「挑战杯」v2：县域农产品（首个案例昭通丑苹果）的 AI 品牌流水线 + 3D 沙盘 + 溯源 H5。
- 四个 Agent：故事/IP、包装设计、内容营销、定价/溯源；一个批次从田间走到消费者。
- 优先级：端到端闭环 > 视觉/交互 > 代码整洁 > 生产运维（并发/真实数据）。
- 面向人的界面与文案一律中文；代码注释不写“怎么调/做什么”类废话。
- 架构取舍先落 `docs/decisions.md`（v2 从 #32 起）；冲突以最新条目为准。

## 当前阶段（2026-10-22）

- **Phase 0 已完成**：开发分支在 `main`；SQLite 9 张表 + Alembic；seed；Mock LLM/Image Provider；`/api/health`、`/api/products`、`/api/batches`、`/api/demo/reset`；React 19 + R3F 9 + Tailwind 4 骨架。
- **Phase 1 已完成**：mock 四 Agent 流水线（story→packaging→marketing→pricing）、`AgentRun`/`Artifact`/workspace、人工审核/驳回/重跑、SSE、站点卡、批次移动。
- **Phase 2 已完成**：真实 LLM Agent（结构化输出 + 失败重试 + mock 兜底）、10 篇知识库 Markdown、FactGuard（逐字引用/违禁词/数字预警）、确定性定价计算器、内置 Noto Serif/Sans + 服务端 PNG 预览、引用/预警/包装预览 UI。
- **Phase 3 已完成**：公开溯源 API（trace / packaging.png / qr.png / scan / chat）、390px H5、扫码统计与 `trace.scanned`、IP 对话边界、固定演示快照（`ZTDEMO26` reset 后仍完整）、3D 包装贴图/广告牌/二维码/CatmullRom 路径/卡车出库。
- **Phase 4 已完成**：真实图像 Provider（Z-Image-Turbo + 缓存 + 插画 artifact）、3 个包装视觉变体、3D 加载/WebGL 错误态、路由与 Scene 代码分割、相机阻尼、空批次新建；短时 1280×720 采样 120fps。
- **Phase 5 已完成**：Playwright 6 条冒烟 + 2 条性能用例、reset 幂等回归、第二产品麻江蓝莓夹具（只建数据，mock 与真实 V4.1-Flash 四站均跑通）、档案化提示词/定价/包装/溯源码前缀、60 秒 58.3fps、200% 等效视口回退、根 `Makefile` 一键启动、runbook。字段级表单与 Docker 明确不做（decisions #63）；LLM 未知字段改为忽略（#64）。
- **下一步交付/补证**：手机真机扫码、包装厂书面报价与食品接触合规、真实盒型/刀版；80–85mm 公开挂牌价与地理标志公告号已补（见 `docs/v2/sources.md`），成交价/同渠道长期价仍可继续跟。
- **尚未实现**：字段级审核表单（明确不做，保留 JSON 编辑器）、真实盒型/刀版、生图失败的视觉兜底、图像缓存清理、手机真机扫码、包装厂书面报价/合规。别假设它们存在。

## 环境特殊性（缺就是缺，别假设有）

- 包管理器：uv（后端）+ pnpm（前端）；不存在 requirements.txt / package-lock。
  已实测：Python 3.13、uv 0.13、Node 24、pnpm 12。
- 数据库：**SQLite**，默认 `backend/data/app.db`（已 gitignore）；不需要 Docker/Postgres。
- `.env`：`backend/.env.example` 复制为 `.env`；`OPENAI_API_KEY` 可空，空则走 Mock；
  `DATABASE_URL` 默认 `sqlite+aiosqlite:///./data/app.db`；`AUTO_APPROVE` 默认 false；
  `LLM_FALLBACK_TO_MOCK=true`、`LLM_TIMEOUT_SECONDS=180`（营销长文实测需要更长超时）；`LLM_THINKING_BUDGET=2048`（128–32768，0 关闭）、`LLM_MAX_TOKENS=4096`。默认模型 `deepseek-ai/DeepSeek-V4.1-Flash`。
  图像：`IMAGE_MODEL=Tongyi-MAI/Z-Image-Turbo`（可切 `Tongyi-MAI/Z-Image`），`IMAGE_SIZE` 空=按调用尺寸自动选 512×512/1024×576/768×1024，`IMAGE_BASE_URL` 空=复用 `OPENAI_BASE_URL`，`IMAGE_TIMEOUT_SECONDS=120`。
- 知识库 `data/knowledge/zhaotong/*.md` 是事实真源（已入库）；seed 时 upsert 到 `knowledge_doc`。
- 包装字体 `backend/src/ruralsmartmark/assets/fonts/` 内置 Noto Serif/Sans SC（OFL，约 40MB）；PNG 不再依赖系统字体。
  运行期包装 PNG 与 IP 插画在 `backend/data/artifacts/`；生图缓存 `backend/data/image-cache/`（均 gitignore）。
- `uv run pytest` **不需要 PG**；测试用临时 SQLite；单函数一样跑。
- 前端测试用本地 `@playwright/test`（不是 vitest/jest）；Chromium 首次 `pnpm exec playwright install chromium`，缓存在 `~/Library/Caches/ms-playwright`。`pnpm test:e2e` 跑桌面/移动冒烟，`pnpm test:perf` 跑 60 秒性能；两者不会提交 `frontend/test-results/`。
- 3D 只在桌面端（≥1024px）；手机只走 `/trace/:code`。3D 构建方式对齐 WareTrack：
  代码拼 Box/Cylinder/Cone/Sphere/Plane + MeshStandardMaterial + Texture；广告牌/二维码用 Html 覆盖层；不引 GLB/写实资产。
- 固定演示批次 `ZT-DEMO-001` / 溯源码 `ZTDEMO26`；`seed/demo_batch.json` 存真实 V4.1 内容快照，`seed/demo_illustration.png` 存 Z-Image-Turbo IP 插画快照；seed/reset 时写入四章产出、4 条 approved run、5 条 artifact（含插画）和确定性定价；reset 后 H5 仍有完整内容。
- 第二产品只做数据夹具 `backend/tests/fixtures/majiang/`，不 seed、不进 UI、不做第二套 3D；输出中的品牌/IP/包装/定价/溯源码前缀从 `ProductProfile.specs` 读取，昭通默认值不变。
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

仓库根（一键）：

- `make dev` → 迁移 + seed + 后端 8000 + 前端 5173；Ctrl-C 一起停
- `make test` → 后端 pytest/ruff + 前端 typecheck/lint/build
- `make e2e` → Playwright 桌面/移动冒烟（未启动的服务由 Playwright 自动拉起）
- `make perf` → 60 秒帧率/堆内存 + 200% 等效视口

后端（在 `backend/`）：

- `uv sync` → 依赖安装（别手动建 venv）
- `uv run alembic upgrade head` → 建表/迁移
- `uv run python -m ruralsmartmark.seed` → 种演示数据（幂等）
- `uv run ruralsmartmark` → 起服务，端口 8000
- `uv run pytest` → 全测试（44 passed + 1 条默认跳过的真实 LLM 冒烟）；单函数：`uv run pytest tests/test_health.py::test_health`
- `RSM_REAL_LLM=1 uv run pytest tests/test_second_product_real.py` → 可选真实 LLM 第二产品冒烟，会消耗额度
- `uv run ruff check .` → 静态检查；`uv run ruff format .` → 格式化

前端（在 `frontend/`）：

- `pnpm install` → 依赖
- `pnpm dev` → 开发服，端口 5173
- `pnpm typecheck` / `pnpm lint` / `pnpm build`
- `pnpm exec playwright install chromium` → 首次安装测试浏览器
- `pnpm test:e2e` → 6 条冒烟；`pnpm test:perf` → 性能用例；`PERF_SECONDS=60 pnpm test:perf` 可指定时长

文档无构建步骤，直接改 `.md`。

## 目录地图（改哪去哪，产物别碰）

```
backend/
  src/ruralsmartmark/
    main.py config.py db.py deps.py models.py schemas.py
    routes/ health.py products.py batches.py demo.py pipeline.py
           knowledge.py artifacts.py trace.py   # 知识库 / 包装文件 / 公开溯源
    agents/ base.py schemas.py prompts.py engine.py runtime.py mock.py orchestrator.py
    providers/ llm.py image.py      # LLM + SiliconFlow 生图 + Mock
    services/ events.py workspace.py knowledge.py fact_guard.py pricing.py packaging.py
             trace.py trace_chat.py # 公开溯源聚合 + IP 对话边界
    assets/fonts/                  # 内置 Noto Serif/Sans + OFL
    seed/ __init__.py __main__.py demo_batch.json demo_illustration.png  # 幂等 seed + 固定演示快照
  migrations/                       # Alembic 生成物，ruff 不检
  alembic.ini pyproject.toml
  tests/ conftest.py test_health.py test_seed.py test_batches.py test_pipeline.py
         test_knowledge.py test_fact_guard.py test_pricing.py test_engine.py
         test_llm.py test_packaging.py test_trace.py test_image.py test_second_product.py
         test_second_product_real.py  # 可选真实 LLM 冒烟（RSM_REAL_LLM=1）
         fixtures/majiang/          # 第二产品档案夹具（只建数据；含 demo 知识库）
data/knowledge/zhaotong/*.md        # 事实源；已入库
frontend/
  src/api/client.ts                 # fetch 封装 + Product/Batch/Knowledge 类型
  src/api/pipeline.ts               # workspace/run/approve/reject + guard 类型
  src/api/trace.ts                  # 公开溯源 / 扫码 / 对话类型与 API
  src/agents.ts                     # Agent 元数据、状态映射、下一站/审核站
  src/stores/world.ts               # Zustand：批次/选中批次
  src/stores/pipeline.ts            # Zustand：workspace/选中 Agent/包装变体/busy
  src/three/Scene.tsx               # 等距场景（包装贴图/广告牌/二维码/路径/卡车）
  src/three/SceneBoundary.tsx       # WebGL/懒加载错误边界
  src/three/stations.ts             # 四站点元数据
  src/components/StationCard.tsx    # 工位卡（预览/引用/FactGuard/包装变体/插画）
  src/components/ReviewDialog.tsx   # 原生 dialog 审核（JSON + 引用/预警/包装预览）
  src/routes/Sandbox.tsx            # 桌面沙盘 `/` + SSE + 审核动线 + 扫码计数
  src/routes/Trace.tsx              # 公开溯源 H5 `/trace/:code`（390px）
  src/App.tsx                       # 路由懒加载（Sandbox / Trace 分包）
  src/styles/global.css             # Tailwind v4 @theme + 山野编辑部 token
  e2e/ sandbox.spec.ts trace.spec.ts perf.spec.ts  # Playwright 冒烟/性能
  playwright.config.ts              # 桌面/移动/perf 三个 project + webServer
  vite.config.ts package.json
docs/
  decisions.md                      # v2 #32 起；唯一决策真源（v1 已移除）
  v2/plan.md                        # v2 产品/架构方案
  v2/ui.md                          # 前端六行契约/token/组件/七类丑
  v2/sources.md                     # 昭通事实待核验清单
  v2/runbook.md                     # 启动/演示动线/验收/新增档案/排障
  05-next-steps.md                  # 唯一动态任务清单
Makefile                            # make dev/test/e2e/perf
.agent/skills/                      # 可复用技能包
```

尚未创建、创建前勿假设存在：字段级审核表单、真实盒型/刀版、生图失败视觉兜底/缓存清理、真实供应商/公告来源。
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
| docs/v2/runbook.md | 启动/演示/验收操作 | 命令、端口、演示动线、新增档案步骤、排障变化时同步 |
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

- 完成一个可验证的工作单元即可自动 commit；任务收口自动 push 到 `origin/main`（2026-10-22 用户授权，不再逐次确认）。
- 例外：force push、重写历史、删除远端分支/标签、提交密钥或生成物，仍必须先说明并等待确认。
- message 格式：`feat|fix|docs|refactor(mN): 一句话结论`。
- 未跑通测试的半成品不提交；不提交 .gitignore 覆盖的产物。

## 常见任务自检（动手前过一眼）

- 改命令/目录/依赖 → 先同步 AGENTS.md，再动代码。
- 改架构决策 → 先落 docs/decisions.md #N，再同步 docs/v2/。
- 结束一轮 → 文档同步了吗？假设补录了吗？红线有违反吗？测试通过并自动提交/推送了吗？

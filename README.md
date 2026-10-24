# 智农云链 · RuralSmartMark

> 正式名：《“智农云链”——基于多智能体协同的县域农产品品牌数字化重构系统》

县域农产品的 AI 品牌流水线：一个产品批次从田间走到消费者，四个 Agent 完成**故事/IP → 包装设计 → 内容营销 → 定价/溯源**；3D 沙盘可视化整条流水线，消费者扫码看溯源 H5。

首个案例：**昭通丑苹果**（云南省昭通市昭阳区）。区域事实可查；合作社、品牌名与人物为演示合成。

## 当前状态（2026-10-22）

**Phase 3–6 已完成**：

- 真实 LLM 四 Agent：故事 → 包装 → 内容 → 定价；Pydantic 结构化输出、失败重试、无 key 或调用失败时降级到演示稿并标注原因。品牌「乌蒙丑果」与 IP「山风守园人」已冻结。
- 10 篇昭通知识库 Markdown；FactGuard 校验逐字引用、违禁认证/功效/保证、数字预警；审核通过前服务端再校验一次。
- 确定性定价计算器：成本、三档价格、毛利、156% 演示溢价与服务端重算；LLM 只写解释。
- 包装合成：内置 Noto Serif/Sans（OFL，约 40MB）渲染 PNG；3D 礼盒正/背面使用该包装图。
- 包装视觉变体：「经典牛皮纸 / 山野红 / 夜绿」，工位可切换，3D 贴图同步；变体只改色板。
- 3D 加载/错误态：`SceneBoundary` + Suspense 骨架；路由与 three.js 分包，手机溯源页不下载 3D chunk。
- 真实图像：SiliconFlow `Tongyi-MAI/Z-Image-Turbo` 生成 IP 插画，审核通过后落 `illustration` artifact，按 prompt hash 缓存；固定演示码使用同 prompt 的快照。
- 公开溯源：`/trace/:code` 390px H5（故事/IP 插画/包装/价格/时间线/IP 对话）、扫码统计、未知码 404；固定演示码 `ZTDEMO26` 在 reset 后仍有完整内容。
- 3D 沙盘：包装贴图、内容广告牌、可点击二维码、CatmullRom 批次路径、卡车出库；扫码数随 SSE 更新。
- 多产品工作台：产品下拉 + 批次按产品过滤；新产品由总控调研/确认后写入，不 seed；旧产品数据保留。
- 单入口总控：右侧「总控」抽屉与 `/controller`；可调研、追问、调用四 Agent、修改/通过/回退；建档/通过/驳回/回退有确认卡（decisions #69）。点「+」先进入空沙盘，产品/批次显示占位，重复点击复用同一个空白会话；建档后切到新批次（#75）。确认通过后自动运行下一站并停在待审核（#74）。头部显示服务端实时的产品/批次/状态，窗口聚焦会重拉上下文。回复走 SSE 流式，思维链默认折叠、展开后一行一条；用户消息发送后立即显示（#72）。
- 调研链路：Firecrawl 异步搜索/抓页 + PydanticAI 工具循环；引用逐字校验；缺字段提问；无 key 时提示贴资料（#70）。检索网络失败自动重试并给中文提示；默认绕过会拖垮长连接的系统代理（`FIRECRAWL_TRUST_ENV=false`）。本机已用真实 Firecrawl 跑通搜索/抓页与麻江蓝莓草案（1 条来源、价格缺失转为追问）。
- 早期站回退：确认后作废下游产出/Artifact，回到目标站重跑，历史 run 保留（#71）。
- 自动化：Playwright 11 条冒烟（含总控面板、独立总控页、空白会话新建产品、流式用户消息/思维链折叠、插画失败兜底）、2 条性能用例；`POST /api/demo/reset` 幂等，扫码数归零且固定码内容不变。
- 性能：1280×720 固定演示批次 60 秒采样 58.3fps，JSHeap 44.5MB→42.4MB；200% 等效视口回退桌面提示且无横向溢出。
- 可复制：第二产品档案夹具「麻江蓝莓」只建数据，mock 四站与真实 V4.1-Flash 四站都跑到 `traced`、`MJ` 溯源码、公开 H5/包装 PNG 可用，真实运行无 fallback、输出无昭通/苹果残留；系统提示、定价标签、包装品牌字、溯源码前缀均从产品档案读取。
- 来源补证：地理标志公告第1478号/登记编号已补；80–85mm 精选果公开挂牌价补了 4 个惠农网页面（5斤 25/36/40 元，10斤 6.2 元/斤）；包装厂只找到 1000 个起订线索，仍无书面报价。
- 一键启动与验收：根 `Makefile` 的 `make dev/test/e2e/perf`；现场演示动线与排障见 [docs/v2/runbook.md](docs/v2/runbook.md)。
- 生图失败兜底：包装工位显示「插画这次没有生成 / 包装审核不受影响」；`python -m ruralsmartmark.maintenance image-cache --dry-run` 可预演 30 天/512MB 缓存清理。
- 后端 64 常跑测试 + 2 条默认跳过的真实外部冒烟、ruff、前端 typecheck/lint/build 全绿；V4.1-Flash 批次 `ZT-2026-005` 真实四站跑到 `ZT0006`（无 fallback），随后 reset 为固定演示数据。

**下一步是交付与补证**：手机真机扫码、包装厂书面报价与食品接触合规、真实盒型/刀版。公开挂牌价与地理标志公告号已补，成交价/同渠道长期价可继续跟。字段级审核表单与 Docker 已确认不做（decisions #63）。

## 快速开始

环境：Python ≥ 3.13、uv ≥ 0.13、Node ≥ 20.19、pnpm ≥ 10。**不需要 Docker/Postgres。**

一键启动（仓库根，自动迁移 + seed + 8000 + 5173）：

```bash
make dev
```

手机真机扫码（需电脑与手机同一 Wi-Fi）：

```bash
make lan    # 自动取局域网 IP、Vite 监听 0.0.0.0、二维码指向局域网地址
```

分开启动：

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
pnpm exec playwright install chromium   # 首次跑 e2e/perf 时
pnpm dev                  # http://127.0.0.1:5173
```

- 桌面沙盘：<http://127.0.0.1:5173/>
- 独立总控：<http://127.0.0.1:5173/controller>
- 公开溯源 H5：<http://127.0.0.1:5173/trace/ZTDEMO26>
- API 文档：<http://127.0.0.1:8000/docs>

Vite 已把 `/api` 代理到 `127.0.0.1:8000`。`OPENAI_API_KEY` 留空时四个 Agent 走确定性 mock；有 key 时调用 OpenAI 兼容端点（默认 SiliconFlow DeepSeek-V4.1-Flash），单次超时 180 秒，`thinking_budget=2048`、`max_tokens=4096`，失败会降级为演示稿并在界面标注原因。同一个 key 也用于图像：默认 `Tongyi-MAI/Z-Image-Turbo`，包装审核通过后生成 IP 插画并缓存；生图失败不影响审核。固定演示批次与溯源码不随 key 变化。

总控调研另需 `FIRECRAWL_API_KEY`（`backend/.env`）。没有搜索 key 时，总控会提示贴来源链接/原文；不会静默编资料。Firecrawl 默认绕过系统代理（`FIRECRAWL_TRUST_ENV=false`），本地代理导致检索 EOF 时可保持默认；必须走代理时设为 `true`。依赖 `pydantic-ai-slim[openai]` 与 `firecrawl-py` 只装在 `backend/.venv`。

## 目录结构

```
Makefile                    # make dev/lan/test/e2e/perf
backend/
  src/ruralsmartmark/       # FastAPI、ORM、四 Agent、总控、知识库/FactGuard、定价/包装
    assets/fonts/           # 内置 Noto Serif/Sans SC + OFL，约 40MB
  migrations/               # Alembic
  tests/                    # 52 常跑测试 + 2 条可选真实外部冒烟 + fixtures/majiang
data/
  knowledge/zhaotong/       # 10 篇事实源 Markdown（入库）
frontend/
  src/three/                # R3F 等距场景
  src/components/           # StationCard / ReviewDialog / ControllerPanel
  src/routes/               # Sandbox / Controller / Trace H5
  src/api/                  # client / pipeline / trace / controller
  src/stores/               # Zustand（产品/批次/流水线）
  src/styles/               # Tailwind v4 + 山野编辑部 token
  e2e/                      # Playwright 冒烟 + perf
  playwright.config.ts      # 桌面/移动/perf projects + webServer
docs/
  decisions.md              # 决策（v2 #32 起）
  v2/plan.md                # v2 产品/架构方案
  v2/ui.md                  # 前端设计契约
  v2/sources.md             # 昭通事实待核验清单
  v2/controller.md          # 总控/多产品契约
  v2/runbook.md             # 启动/演示/验收/新增档案/排障
  05-next-steps.md          # 当前进度与下一步
```

## 常用命令

| 位置 | 命令 | 说明 |
| --- | --- | --- |
| 根 | `make dev` | 迁移 + seed + 后端 8000 + 前端 5173 |
| 根 | `make lan` | 局域网扫码模式（0.0.0.0 + 局域网二维码；仅可信网络） |
| 根 | `make test` | 后端 52 tests/ruff + 前端 typecheck/lint/build |
| 根 | `make e2e` / `make perf` | Playwright 冒烟 / 60 秒性能 |
| backend | `uv run ruralsmartmark` | 启动开发服务 |
| backend | `uv run pytest` | 后端测试（临时 SQLite；64 passed + 2 skipped） |
| backend | `uv run python -m ruralsmartmark.maintenance image-cache --dry-run` | 生图缓存清理预演（30 天/512MB） |
| backend | `RSM_REAL_LLM=1 uv run pytest tests/test_second_product_real.py` | 可选真实 LLM 第二产品冒烟（消耗额度） |
| backend | `RSM_REAL_SEARCH=1 uv run pytest tests/test_search_real.py` | 可选真实 Firecrawl 搜索/抓页（消耗 credits） |
| backend | `uv run ruff check .` | 静态检查 |
| backend | `uv run alembic upgrade head` | 迁移 |
| backend | `uv run python -m ruralsmartmark.seed` | 幂等 seed |
| frontend | `pnpm dev` | 开发服 |
| frontend | `pnpm typecheck` / `pnpm lint` / `pnpm build` | 前端检查/构建 |
| frontend | `pnpm test:e2e` / `pnpm test:perf` | 9 条冒烟 / 2 条性能用例 |

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查（含 DB） |
| GET | `/api/products` | 产品档案 |
| GET | `/api/knowledge` | 知识库清单（引用 chips 用） |
| GET | `/api/batches?product_id=` | 批次列表（可按产品过滤） |
| POST | `/api/batches` | 新建批次 |
| POST | `/api/controller/sessions` | 创建/获取总控会话 |
| GET | `/api/controller/sessions/{id}` | 总控会话、消息、草案、待确认动作 |
| POST | `/api/controller/sessions/{id}/messages` | 发给总控（非流式，调研/读取/运行 Agent） |
| POST | `/api/controller/sessions/{id}/messages/stream` | 流式发给总控（SSE：user/thinking/delta/tool/done/error） |
| POST | `/api/controller/sessions/{id}/confirm` | 确认/取消建档、通过、驳回、回退 |
| GET | `/api/batches/{id}` | 批次详情 |
| GET | `/api/batches/{id}/workspace` | 批次 + 运行记录 + 产出物 |
| POST | `/api/batches/{id}/pipeline/start` | 运行下一步 |
| POST | `/api/batches/{id}/agents/{agent}/run` | 重跑当前 Agent |
| POST | `/api/batches/{id}/agents/{agent}/approve` | 审核通过（服务端二次 FactGuard/定价重算） |
| POST | `/api/batches/{id}/agents/{agent}/reject` | 驳回 |
| GET | `/api/batches/{id}/agents/packaging/preview` | 包装 PNG 预览（服务端渲染，`?variant=`） |
| GET | `/api/batches/{id}/agents/packaging/variants` | 包装变体权威列表 |
| GET | `/api/artifacts/{id}/file` | 审核后的包装 PNG / IP 插画 |
| GET | `/api/batches/{id}/events` | SSE 实时事件 |
| GET | `/api/batches/by-code/{code}` | 按批次码查 |
| GET | `/api/trace/{code}` | 公开溯源数据（故事/包装/价格/时间线/扫码数） |
| GET | `/api/trace/{code}/packaging.png` | 溯源页包装图 |
| GET | `/api/trace/{code}/qr.png` | 溯源二维码 |
| GET/POST | `/api/trace/{code}/scan` | 读取/写入扫码事件 |
| POST | `/api/trace/{code}/chat` | IP 对话（边界拒答 + 模板兜底） |
| POST | `/api/demo/reset` | 重置演示批次（固定码内容保留） |

## 设计方向

- 「山野编辑部」：暖色纸感、衬线标题、低多边形乡村；不是 WMS 冷色控制塔。
- 3D 构建对齐 WareTrack：代码拼低多边形几何体 + 平面材质 + Texture；广告牌/二维码用 Html 覆盖层保证中文与二维码清晰；不引 GLB/写实资产。
- 桌面看 3D 沙盘，手机只看扫码溯源 H5。
- 多产品列表/切换；不做游戏化、登录/权限、真实电商 API、Canva/Midjourney、IoT 温度曲线。

## 文档

- [AGENTS.md](AGENTS.md) — AI 协作约束（人类可跳过）
- [docs/v2/plan.md](docs/v2/plan.md) — 完整方案
- [docs/v2/ui.md](docs/v2/ui.md) — 前端设计契约
- [docs/v2/sources.md](docs/v2/sources.md) — 昭通事实待核验清单
- [docs/v2/controller.md](docs/v2/controller.md) — 总控/多产品契约
- [docs/v2/runbook.md](docs/v2/runbook.md) — 启动、演示动线、验收与排障
- [docs/decisions.md](docs/decisions.md) — 决策记录
- [docs/05-next-steps.md](docs/05-next-steps.md) — 当前进度与下一步

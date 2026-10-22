# 乡土印记 v2 · RuralSmartMark

县域农产品的 AI 品牌流水线：一个产品批次从田间走到消费者，四个 Agent 完成**故事/IP → 包装设计 → 内容营销 → 定价/溯源**；3D 沙盘可视化整条流水线，消费者扫码看溯源 H5。

首个案例：**昭通丑苹果**（云南省昭通市昭阳区）。区域事实可查；合作社、品牌名与人物为演示合成。

## 当前状态（2026-10-21）

**Phase 2 已完成**：

- 真实 LLM 四 Agent：故事 → 包装 → 内容 → 定价；Pydantic 结构化输出、失败重试、无 key 或调用失败时降级到演示稿并标注原因。
- 10 篇昭通知识库 Markdown；FactGuard 校验逐字引用、违禁认证/功效/保证、数字预警；审核通过前服务端再校验一次。
- 确定性定价计算器：成本、三档价格、毛利、156% 演示溢价与服务端重算；LLM 只写解释。
- 包装合成：内置 Noto Serif/Sans（OFL，约 40MB）渲染 PNG，预览接口直接返回服务端 PNG；审核通过后落盘，二维码指向 `/trace/:code`（H5 内容在 Phase 3）。
- 前端 React 19 + R3F 9 + Tailwind 4：3D 沙盘、工位卡（引用/预警/包装预览）、JSON 审核弹窗、批次沿站点移动、KPI/产出物 Tabs。
- 后端 29 测试、ruff、前端 typecheck/lint/build 全绿；真实 DeepSeek-V3.1-Terminus 批次 `ZT-2026-001` 跑通到 `traced`；切换后的 V4.1-Flash 已验证故事/包装 Agent，旧 `traced` 批次未用新模型重跑。mock 动线仍可跑。

**Phase 3 下一步**：3D 包装贴图/广告牌/二维码联动 + 公开溯源 API/H5 + IP 对话。真实图像 Provider、字段级审核表单、扫码统计写入尚未实现。

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

Vite 已把 `/api` 代理到 `127.0.0.1:8000`。`OPENAI_API_KEY` 留空时四个 Agent 走确定性 mock；有 key 时调用 OpenAI 兼容端点（默认 SiliconFlow DeepSeek-V4.1-Flash），单次超时 180 秒，`thinking_budget=2048`、`max_tokens=4096`，失败会降级为演示稿并在界面标注原因。固定演示批次与溯源码不随 key 变化。

## 目录结构

```
backend/
  src/ruralsmartmark/       # FastAPI、ORM、四 Agent、知识库/FactGuard、定价/包装
    assets/fonts/           # 内置 Noto Serif/Sans SC + OFL，约 40MB
  migrations/               # Alembic
  tests/                    # health / seed / pipeline / knowledge / guard / pricing / engine / fonts
data/
  knowledge/zhaotong/       # 10 篇事实源 Markdown（入库）
frontend/
  src/three/                # R3F 等距场景
  src/components/           # StationCard / ReviewDialog
  src/routes/               # Sandbox / Trace
  src/stores/               # Zustand
  src/styles/               # Tailwind v4 + 山野编辑部 token
docs/
  decisions.md              # 决策（v2 #32 起）
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

## 接口（Phase 2）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查（含 DB） |
| GET | `/api/products` | 产品档案 |
| GET | `/api/knowledge` | 知识库清单（引用 chips 用） |
| GET | `/api/batches` | 批次列表 |
| POST | `/api/batches` | 新建批次 |
| GET | `/api/batches/{id}` | 批次详情 |
| GET | `/api/batches/{id}/workspace` | 批次 + 运行记录 + 产出物 |
| POST | `/api/batches/{id}/pipeline/start` | 运行下一步 |
| POST | `/api/batches/{id}/agents/{agent}/run` | 重跑当前 Agent |
| POST | `/api/batches/{id}/agents/{agent}/approve` | 审核通过（服务端二次 FactGuard/定价重算） |
| POST | `/api/batches/{id}/agents/{agent}/reject` | 驳回 |
| GET | `/api/batches/{id}/agents/packaging/preview` | 包装 PNG 预览（服务端渲染） |
| GET | `/api/artifacts/{id}/file` | 审核后的包装 PNG |
| GET | `/api/batches/{id}/events` | SSE 实时事件 |
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

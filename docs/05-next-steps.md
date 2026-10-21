# 05 · 下一步任务清单（v2）

> 状态：🟢 Phase 1 已完成（2026-10-21）；下一步 Phase 2
> 更新时间：2026-10-21
> 用法：完成一项就在「当前进度」打勾；决策变化先改 [decisions.md](decisions.md) 的 v2 段（#32 起）
> 注意：本文是 v2；v1 的 M0–M6 记录只保留在 git history 与旧 docs 中

## 0. 当前进度（截至 2026-10-21）

- [x] `rewrite/v2` 分支；旧 v1 backend/frontend 移出工作树（`main` 保留历史）
- [x] SQLite + 9 张表 ORM（product / batch / agent_run / artifact / knowledge_doc / benchmark / kol / scan_event / chat_message）
- [x] Alembic 初始迁移 `47f2487c3523_initial_v2_schema.py`
- [x] 幂等 seed：昭通丑苹果 + 3 条知识库占位 + 3 条价格基准 + 批次 `ZT-DEMO-001` / `ZT-2026-001`
- [x] Mock LLM Provider + Mock Image Provider（无 key 可跑）
- [x] FastAPI `/api/health` / `/api/products` / `/api/batches` / `/api/demo/reset`
- [x] 后端测试 8 条（Phase 0 4 + Phase 1 4）+ `ruff check` 零告警
- [x] 前端 React 19 + R3F 9 + Tailwind 4 骨架；Zustand 批次状态
- [x] 3D 场景：果园、四站点、批次托盘、卡车、五个标签；桌面端提示；`/trace` 骨架
- [x] `pnpm typecheck` / `lint` / `build` 全绿；1280×720 与 390×844 视觉验收
- [x] **Phase 1 · Walking skeleton（全 mock）**：四 Agent 状态机 + 审核/驳回/重跑 + SSE + 工位卡 + 批次移动；8 后端测试全绿。
- [ ] Phase 2 · 真实 Agent
- [ ] Phase 3 · 沙盘联动 + 溯源 H5
- [ ] Phase 4 · 图像与视觉打磨
- [ ] Phase 5 · 加固与交付

## 1. Phase 1 · Walking skeleton（全 mock）

目标：不配任何 key，点「运行流水线」就能走完六步；刷新/重连状态不丢。

### 1.1 后端

- [x] `agents/orchestrator.py`：批次状态机 `raw → story → packaging → marketing → pricing → traced`
- [x] `routes/pipeline.py`：`POST /api/batches/{id}/pipeline/start`、`POST /api/batches/{id}/agents/{agent}/run`、`approve/reject`
- [x] Mock 产出：故事/包装/内容/定价四段 JSON，写入 `agent_run` + `artifact` + `batch.*_json`
- [x] 人工审核门：`waiting_review` 状态；批准后推进；驳回保留内容
- [x] SSE：`GET /api/batches/{id}/events`；单 `message` 事件 + `type` 字段；`sse-starlette` ping 保活
- [x] 测试：状态机流转、批准推进、驳回重跑；SSE 由浏览器实测

### 1.2 前端

- [x] 顶栏「运行流水线」按钮接 API；运行中/待审核/失败的按钮态
- [x] 右栏站点卡：Agent 状态、输入摘要、产出预览、运行/重跑/审核
- [x] 审核 `<dialog>`：可编辑字段；通过/驳回；Esc/遮罩关闭
- [x] 产出物 Tabs：故事/包装/内容/定价/溯源计数与预览
- [x] 批次沿站点位置缓动；站点状态点/完成色
- [x] KPI 随 SSE 更新；断线重连后重拉快照
- [x] 浏览器手动冒烟（1280×720）：运行 → 四产出 → 审核 → 批次移动

### 1.3 验收

```bash
cd backend && uv run pytest && uv run ruff check .
cd frontend && pnpm typecheck && pnpm lint && pnpm build
# 浏览器：不配 key，点运行 → 四步审核 → 批次移动 → 溯源骨架
```

### 1.4 验收记录（2026-10-21）

- `uv run pytest` 8 passed；`uv run ruff check .` 零告警。
- `pnpm typecheck` / `lint` / `build` 全绿。
- 浏览器：batch 2 四步审核 → `traced`（四产出）；batch 3 story approved → `packaging_review`；审核后自动选中下一站。

## 2. Phase 2 · 真实 Agent（简报）

- [ ] Agent 1 故事/IP：知识库注入 + 引用校验 + 人工润色
- [ ] Agent 2 包装：结构化 JSON + SVG/Pillow 合成 + 3D 盒贴图
- [ ] Agent 3 内容：小红书/抖音/微信/客服 Q&A/KOL Brief
- [ ] Agent 4 定价/溯源：确定性计算器 + 基准价 + 二维码 + 时间线
- [ ] `FactGuard`：年份/百分比/认证/人名/引用校验；未通过阻断
- [ ] 真实 LLM 接入（`OPENAI_*`，默认 SiliconFlow DeepSeek；空 key 走 mock）
- [ ] 测试：每 Agent schema 校验、引用存在、违规 claim 拦截

## 3. Phase 3 · 沙盘联动 + 溯源 H5（简报）

- [ ] 站点/批次/门店点击 → 右栏上下文卡
- [ ] 包装贴图替换纸箱；广告牌显示内容；二维码出现在礼盒/门店
- [ ] 批次沿 CatmullRom 路径移动；卡车出库
- [ ] `/trace/:code`：公开 API + 故事/时间线/价格/IP 对话
- [ ] 390px 手机验收；二维码跟随当前 origin
- [ ] 测试：公开溯源、未知码 404、对话边界

## 4. Phase 4 · 图像与视觉打磨（简报）

- [ ] SiliconFlow 图像 Provider（真实生图 + 本地缓存 + 失败兜底）
- [ ] 包装变体/盒型；3D 场景材质、阴影、相机缓动
- [ ] 空态/错误态/加载态；1280×720 60fps；DPR 上限 2
- [ ] 七类丑自检逐项记录 pass/fixed/known-gap
- [ ] 代码分割（当前 bundle ~1.2MB 警告）

## 5. Phase 5 · 加固与交付（简报）

- [ ] 单元/集成/Playwright 冒烟
- [ ] `POST /api/demo/reset` 幂等；固定码 `ZTDEMO26` 不变
- [ ] 第二产品档案测试（麻江蓝莓夹具，证明换档案不改代码）
- [ ] Docker/一键启动（可选）
- [ ] AGENTS / README / decisions / v2 docs 收口
- [ ] 演示脚本与彩排（等开发完成后再做）

## 6. 未验证假设（开工即验证）

- [ ] 昭通丑苹果事实：国家地理标志公告号/年份、海拔 1800–2500m、糖度 14–15.7%、散装 3.5–6.2 元/斤、礼盒 8.7–14.5 元/斤；当前 `source_url` 为 TODO，见 [v2/sources.md](v2/sources.md)
- [ ] 真实 LLM key 是否可用；空 key mock 路径已跑通
- [ ] SiliconFlow 图像模型/额度/水印设置（Phase 4 前核验）
- [ ] 3D 场景在目标演示机的 60fps（当前 1280×720 已看，未做长时压测）
- [ ] 手机真机扫码（当前只验了 390px 视口）
- [ ] 包装印刷成本/小批量报价（Agent 2 成本估算需要）
- [ ] 真实价格行情（当前全部标“演示测算”）

## 7. 已知缺口（Phase 0 结束时的诚实清单）

- 真实 Agent、公开溯源 API/IP 对话、包装合成、定价计算、真实图像生成**还没有**；Phase 1 的 mock 流水线、SSE、审核与工位卡已通。
- 3D 场景仍是风格化骨架：四站点/果园/批次/卡车/站点状态/批次移动已通，建筑与树木细节待 Phase 4。
- 前端 bundle 约 1.2MB（three.js 占大头）；Phase 4 再做代码分割。
- v1 设计文档已移除；如需追溯见 git history（main 分支）。
- `docs/v2/sources.md` 里的昭通事实尚未逐条核验；故事/定价前必须补齐。

## 8. 验收命令（当前）

```bash
# backend
cd backend
uv run alembic upgrade head
uv run python -m ruralsmartmark.seed
uv run pytest
uv run ruff check .

# frontend
cd frontend
pnpm typecheck
pnpm lint
pnpm build
```

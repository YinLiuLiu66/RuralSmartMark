# 05 · 下一步任务清单（v2）

> 状态：🟢 Phase 2 已完成（2026-10-21）；下一步 Phase 3
> 更新时间：2026-10-21
> 用法：完成一项就在「当前进度」打勾；决策变化先改 [decisions.md](decisions.md) 的 v2 段（#32 起）
> 注意：本文是 v2；v1 的 M0–M6 记录只保留在 git history 与旧 docs 中

## 0. 当前进度（截至 2026-10-21）

- [x] `rewrite/v2` 分支；旧 v1 backend/frontend 移出工作树（`main` 保留历史）
- [x] SQLite + 9 张表 ORM + Alembic 迁移（含 `agent_run.guard_json`）
- [x] 幂等 seed：昭通丑苹果 + 10 篇知识库 + 3 条价格基准 + 批次 `ZT-DEMO-001` / `ZT-2026-001`
- [x] Mock LLM Provider + Mock Image Provider（无 key 可跑）
- [x] **Phase 0/1**：沙盘骨架、四 Agent 状态机、审核/驳回/重跑、SSE、工位卡、批次移动
- [x] **Phase 2**：真实 LLM Agent + 知识库 + FactGuard + 确定性定价 + 内置字体包装 PNG + 引用/预警/预览 UI
- [x] 后端测试 29 条 + `ruff check` 零告警
- [x] 前端 React 19 + R3F 9 + Tailwind 4；`pnpm typecheck/lint/build` 全绿
- [x] 真实 DeepSeek-V3.1-Terminus 批次 `ZT-2026-001` 走到 `traced`（`ZT0002`，156% 演示溢价）；切换后的 V4.1-Flash 已验证故事/包装 Agent，旧 `traced` 批次未重跑；mock 动线仍可跑
- [ ] Phase 3 · 沙盘联动 + 溯源 H5
- [ ] Phase 4 · 图像与视觉打磨
- [ ] Phase 5 · 加固与交付

## 1. Phase 1 · Walking skeleton（已完成，摘要）

目标：不配任何 key，点「运行流水线」就能走完六步；刷新/重连状态不丢。

- [x] 状态机 `raw → story → packaging → marketing → pricing → traced`
- [x] `pipeline/start`、`agents/{agent}/run`、`approve/reject`；人工审核门
- [x] SSE 单 `message` 事件 + `type`；浏览器断线重连后重拉 workspace
- [x] 工位卡、JSON 审核 dialog、产出物 Tabs、批次沿站点移动
- [x] 浏览器手动冒烟：四步审核 → `traced`；审核后自动启动并选中下一站

## 2. Phase 2 · 真实 Agent（已完成）

### 2.1 知识库与事实

- [x] `data/knowledge/zhaotong/*.md` 10 篇，frontmatter 含 `source_url/source_date/credibility`
- [x] seed 时 upsert 到 `knowledge_doc`；`knowledge_dir` 由产品档案指定
- [x] 第一轮来源核验：GI-01/ORIGIN-01/ORIGIN-02/ENV-01/ENV-02/CUL-01/PRICE-01 可引用；具体海拔、1940/吴敬端、洒渔 13.1 万亩等未核项 DROP
- [x] `docs/v2/sources.md` 记录 OK/CONFLICT/TODO/DEMO/DROP 与原文摘录

### 2.2 真实 Agent

- [x] Pydantic 输出模型（故事/包装/内容/定价）+ JSON Schema 注入
- [x] 真实 LLM 调用（OpenAI 兼容；默认 SiliconFlow DeepSeek），`model/tokens` 落 `AgentRun`
- [x] 校验失败/事实违规重试 1 次；仍失败或调用失败时 mock 降级并标 `demo/fallback_reason`
- [x] 定价 Agent：确定性计算器出数字，LLM 只写解释；解释数字不一致时用模板
- [x] 审核通过前服务端二次 FactGuard；定价数字按计算器重算

### 2.3 包装合成

- [x] `services/packaging.py`：内置 Noto Serif/Sans，服务端 PNG 预览 + 落盘（1600×1000，固定品牌色角色）
- [x] `GET /api/batches/{id}/agents/packaging/preview`、`GET /api/artifacts/{id}/file`
- [x] 审核通过后落盘；定价生成溯源码后重渲染最终二维码

### 2.4 前端

- [x] 工位卡专用预览：故事摘要/包装图/内容卡片/价格梯+公式
- [x] 引用 chips（外链 source_url；演示条目标“演示”）、FactGuard 预警、模型/tokens
- [x] 审核 dialog：引用/预警/包装预览 + JSON 编辑 + 驳回备注
- [x] `/api/knowledge` 供引用 chips 使用；API 请求禁用缓存，避免审核后看到旧产出

### 2.5 验收记录（2026-10-21）

```bash
cd backend && uv run pytest && uv run ruff check .
cd frontend && pnpm typecheck && pnpm lint && pnpm build
```

- `uv run pytest` 29 passed；`uv run ruff check .` 零告警。
- `pnpm typecheck` / `lint` / `build` 全绿（bundle ~1.24MB，Phase 4 拆包）。
- 真实 DeepSeek：`ZT-2026-001` 故事/包装/内容/定价四步均 `waiting_review` → 批准 → `traced`；`ZT0002`，礼盒 ¥128/5kg，溢价 156%，二维码指向 `/trace/ZT0002`。
- 真实营销 Agent 首次 90s 超时降级；提高到 180s 后成功。超时是真实风险，已在 `.env.example` 固定 180。
- 浏览器：引用外链可点、FactGuard 预警可见、包装 PNG 预览正常、审核后再校验拦截验证通过（pytest）。

## 3. Phase 3 · 沙盘联动 + 溯源 H5（简报）

- [ ] 包装 PNG 贴到 3D 礼盒；广告牌显示小红书标题；二维码出现在礼盒/门店
- [ ] 批次沿 CatmullRom 路径移动；卡车出库；站点状态与真实 run 对齐
- [ ] `/api/trace/{code}`：批次、四章产出、价格公式、时间线；未知码 404
- [ ] `/trace/:code` H5：故事/包装/价格/IP 对话；390px 验收
- [ ] 扫码统计写 `scan_event`；`/api/trace/{code}/scan`
- [ ] IP 对话只使用已批准故事/知识库，拒绝功效/未认证问题
- [ ] 测试：公开溯源、未知码、对话边界

## 4. Phase 4 · 图像与视觉打磨（简报）

- [ ] SiliconFlow 图像 Provider（真实生图 + 缓存 + 失败兜底）
- [ ] 包装变体/盒型；3D 材质、阴影、相机缓动
- [ ] 空态/错误态/加载态；1280×720 60fps；DPR 上限 2
- [ ] 七类丑自检逐项记录 pass/fixed/known-gap
- [ ] 代码分割（当前 bundle ~1.24MB 警告）

## 5. Phase 5 · 加固与交付（简报）

- [ ] Playwright 冒烟（当前为浏览器手动验收）
- [ ] `POST /api/demo/reset` 幂等；固定码 `ZTDEMO26` 不变
- [ ] 第二产品档案测试（麻江蓝莓夹具，证明换档案不改代码）
- [ ] Docker/一键启动（可选）
- [ ] AGENTS / README / decisions / v2 docs 收口
- [ ] 演示脚本与彩排

## 6. 未验证假设（开工即验证）

- [x] 真实 LLM key 可用；空 key mock 路径已跑通
- [x] 营销长文需要比 90s 更长的超时；已改 180s
- [ ] SiliconFlow 图像模型/额度/水印设置（Phase 4 前核验）
- [ ] 3D 场景在目标演示机的长时 60fps（当前 1280×720 已看，未做长时压测）
- [ ] 手机真机扫码（当前只验了 390px 视口）
- [ ] 包装印刷成本/小批量报价（当前 5.7 元/盒为演示估算）
- [ ] 80–85mm 精选果的同规格、同渠道价格（至少 3 家）
- [ ] 地理标志公告原文/公告号（当前用协会页 + 云南日报/昭通新闻网）

## 7. 已知缺口（Phase 2 结束时的诚实清单）

- 公开溯源 API/IP 对话、3D 包装贴图、真实图像 Provider、字段级审核表单、扫码统计写入**还没有**。
- 定价 156% 与包装成本 5.7 元/盒是演示测算；页面已标“演示测算”。
- 故事/内容里的区域事实已尽量引用知识库，但 LLM 仍可能写未引用的概括（FactGuard 对未引用数字只给 warning）；审核时看引用与预警。
- 前端 bundle 约 1.24MB（three.js 占大头）；Phase 4 再做代码分割。
- v1 设计文档已移除；如需追溯见 git history（main 分支）。

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

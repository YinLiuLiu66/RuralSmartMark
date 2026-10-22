# 05 · 下一步任务清单（v2）

> 状态：🟢 Phase 3 已完成（2026-10-22）；下一步 Phase 4
> 更新时间：2026-10-22
> 用法：完成一项就在「当前进度」打勾；决策变化先改 [decisions.md](decisions.md) 的 v2 段（#32 起）
> 注意：本文是 v2；v1 的 M0–M6 记录只保留在 git history 与旧 docs 中

## 0. 当前进度（截至 2026-10-22）

- [x] 开发分支切回 `main`（`rewrite/v2` 已合并并删除）；旧 v1 backend/frontend 移出工作树
- [x] SQLite + 9 张表 ORM + Alembic 迁移（含 `agent_run.guard_json`）
- [x] 幂等 seed：昭通丑苹果 + 10 篇知识库 + 3 条价格基准 + 批次 `ZT-DEMO-001` / `ZT-2026-001`
- [x] Mock LLM Provider + Mock Image Provider（无 key 可跑）
- [x] **Phase 0/1**：沙盘骨架、四 Agent 状态机、审核/驳回/重跑、SSE、工位卡、批次移动
- [x] **Phase 2**：真实 LLM Agent + 知识库 + FactGuard + 确定性定价 + 内置字体包装 PNG + 引用/预警/预览 UI
- [x] **Phase 3**：公开溯源 API + 390px H5 + 扫码统计 + IP 对话边界 + 固定演示快照 + 3D 包装贴图/广告牌/二维码/CatmullRom/卡车
- [x] 后端测试 39 条 + `ruff check` 零告警
- [x] 前端 React 19 + R3F 9 + Tailwind 4；`pnpm typecheck/lint/build` 全绿
- [x] V4.1-Flash 批次 `ZT-2026-005` 真实四站跑到 `ZT0006`（故事/包装/营销/定价 tokens 4925/12667/9059/4126，均无 fallback）；随后 reset 为固定演示数据
- [x] 固定演示批次 `ZT-DEMO-001` 在 reset 后仍有完整四章产出、4 条 approved run/artifact、`ZTDEMO26` H5、扫码/对话
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

- `uv run pytest` 29 passed（Phase 2 当时；Phase 3 为 38 passed）；`uv run ruff check .` 零告警。
- `pnpm typecheck` / `lint` / `build` 全绿（Phase 2 当时 bundle ~1.24MB；Phase 3 为 ~1.27MB，Phase 4 拆包）。
- 真实 DeepSeek：`ZT-2026-001` 故事/包装/内容/定价四步均 `waiting_review` → 批准 → `traced`；`ZT0002`，礼盒 ¥128/5kg，溢价 156%，二维码指向 `/trace/ZT0002`。
- 真实营销 Agent 首次 90s 超时降级；提高到 180s 后成功。超时是真实风险，已在 `.env.example` 固定 180。
- 浏览器：引用外链可点、FactGuard 预警可见、包装 PNG 预览正常、审核后再校验拦截验证通过（pytest）。

## 3. Phase 3 · 沙盘联动 + 溯源 H5（已完成，2026-10-22）

- [x] 包装 PNG 贴到 3D 礼盒正/背面；广告牌显示小红书标题；二维码立牌可点击打开 H5
- [x] 批次沿 CatmullRom 路径移动；卡车出库；站点状态与真实 run 对齐
- [x] `/api/trace/{code}`：批次、四章产出、引用、价格公式、时间线、扫码数；未知码 404
- [x] `/trace/:code` H5：故事/包装/价格/时间线/内容/IP 对话；390px 验收
- [x] 扫码统计写 `scan_event`；`GET|POST /api/trace/{code}/scan`；SSE `trace.scanned`
- [x] IP 对话只使用已批准故事/包装/定价与引用证据，拒绝功效/认证/保证问题；LLM 回复再过 FactGuard + 数字白名单
- [x] 测试：公开溯源、未知码、包装图/二维码、扫码计数、对话边界
- [x] 固定演示快照：`seed/demo_batch.json` + reset 后 `ZTDEMO26` 完整可用
- [x] 验证：39 tests / ruff / typecheck / lint / build；H5 390×844 与 320px 截图；沙盘 1280×720 截图；二维码按钮打开新标签

## 3.1 Phase 3 验收记录

- 真实 V4.1-Flash 批次 `ZT-2026-005` 四站到 `ZT0006`：故事 4925 tokens、包装 12667、营销 9059、定价 4126；均无 fallback。
- 首次包装降级已定位为事实校验失败，重跑通过；营销首次因 DEMO-02 降级，补强提示词后通过；第二次因 COMP-06 误伤提问，修正规则后通过。
- reset 后 `ZTDEMO26`：故事/包装/内容/定价齐全，时间线四段审核，扫码/对话可用；`ZT0006` 按预期 404。
- 3D：礼盒红/奶油标签、广告牌标题、二维码、卡车出库可见；二维码按钮打开 `/trace/ZTDEMO26`。

## 4. Phase 4 · 图像与视觉打磨（简报）

- [ ] SiliconFlow 图像 Provider（真实生图 + 缓存 + 失败兜底）
- [ ] 包装变体/盒型；3D 材质、阴影、相机缓动
- [ ] 空态/错误态/加载态；1280×720 60fps；DPR 上限 2
- [x] 七类丑自检逐项记录 pass/fixed/known-gap（H5 + 沙盘，见 ui.md §6）
- [ ] 代码分割（当前 bundle ~1.27MB 警告）

## 5. Phase 5 · 加固与交付（简报）

- [ ] Playwright 冒烟（当前为浏览器手动验收）
- [ ] `POST /api/demo/reset` 幂等；固定码 `ZTDEMO26` 不变
- [ ] 第二产品档案测试（麻江蓝莓夹具，证明换档案不改代码）
- [ ] 字段级审核表单（可选，decisions #58）
- [ ] Docker/一键启动（可选）
- [ ] AGENTS / README / decisions / v2 docs 收口
- [ ] 演示脚本与彩排

## 6. 未验证假设（开工即验证）

- [x] 真实 LLM key 可用；空 key mock 路径已跑通
- [x] 营销长文需要比 90s 更长的超时；已改 180s
- [x] V4.1-Flash 全链路可用：营销/定价也不再超时或数字不一致
- [x] 固定演示码 reset 后仍有完整内容（seed 快照 + 4 run/artifact）
- [x] H5 390px/320px 无横向溢出；二维码按钮可打开 H5
- [ ] SiliconFlow 图像模型/额度/水印设置（Phase 4 前核验）
- [ ] 3D 场景在目标演示机的长时 60fps（当前 1280×720 已看，未做长时压测）
- [ ] 手机真机扫码（当前只验了 390px 视口）
- [ ] 200% zoom 与超长批次码 H5 压测
- [ ] 包装印刷成本/小批量报价（当前 5.7 元/盒为演示估算）
- [ ] 80–85mm 精选果的同规格、同渠道价格（至少 3 家）
- [ ] 地理标志公告原文/公告号（当前用协会页 + 云南日报/昭通新闻网）

## 7. 已知缺口（Phase 3 结束时的诚实清单）

- 真实图像 Provider、字段级审核表单、Playwright、第二产品档案夹具**还没有**。
- 定价 156% 与包装成本 5.7 元/盒是演示测算；页面已标“演示测算”。
- 故事/内容里的区域事实已尽量引用知识库，但 LLM 仍可能写未引用的概括（FactGuard 对未引用数字只给 warning）；审核时看引用与预警。
- IP 对话只做了关键词/规则 + LLM 后置校验；没有多轮上下文管理、没有真人客服兜底。
- 前端 bundle 约 1.27MB（three.js 占大头）；Phase 4 再做代码分割。
- 200% zoom、超长批次码、长时 60fps/内存尚未压测。
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

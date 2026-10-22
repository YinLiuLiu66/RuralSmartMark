# 05 · 下一步任务清单（v2）

> 状态：🟢 Phase 6 已完成（2026-10-22，真实 Firecrawl 已验）；外部实物补证待做
> 更新时间：2026-10-22
> 用法：完成一项就在「当前进度」打勾；决策变化先改 [decisions.md](decisions.md) 的 v2 段（#32 起）
> 注意：本文是 v2；v1 的 M0–M6 记录只保留在 git history 与旧 docs 中

## 0. 当前进度（截至 2026-10-22）

- [x] 开发分支切回 `main`（`rewrite/v2` 已合并并删除）；旧 v1 backend/frontend 移出工作树
- [x] SQLite + 11 张表 ORM + Alembic 迁移（含 `agent_run.guard_json`、controller 两表）
- [x] 幂等 seed：昭通丑苹果 + 10 篇知识库 + 3 条价格基准 + 批次 `ZT-DEMO-001` / `ZT-2026-001`
- [x] Mock LLM Provider + Mock Image Provider（无 key 可跑）
- [x] **Phase 0/1**：沙盘骨架、四 Agent 状态机、审核/驳回/重跑、SSE、工位卡、批次移动
- [x] **Phase 2**：真实 LLM Agent + 知识库 + FactGuard + 确定性定价 + 内置字体包装 PNG + 引用/预警/预览 UI
- [x] **Phase 3**：公开溯源 API + 390px H5 + 扫码统计 + IP 对话边界 + 固定演示快照 + 3D 包装贴图/广告牌/二维码/CatmullRom/卡车
- [x] 后端测试 52 条常跑 + 2 条默认跳过的真实外部冒烟 + `ruff check` 零告警
- [x] 前端 React 19 + R3F 9 + Tailwind 4；`pnpm typecheck/lint/build` 全绿
- [x] V4.1-Flash 批次 `ZT-2026-005` 真实四站跑到 `ZT0006`（故事/包装/营销/定价 tokens 4925/12667/9059/4126，均无 fallback）；随后 reset 为固定演示数据
- [x] 固定演示批次 `ZT-DEMO-001` 在 reset 后仍有完整四章产出、4 条 approved run、5 条 artifact（含插画）、`ZTDEMO26` H5、扫码/对话
- [x] Phase 4 · 图像与视觉打磨（图像 Provider / 变体 / 加载态 / 拆包）
- [x] Phase 5 · 加固与交付（Playwright / reset 幂等 / 第二产品夹具 / 60 秒性能 / make dev / runbook）
- [x] Phase 6 · 多产品 + 单入口总控 + Firecrawl 调研 + 早期站回退（代码侧）

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

## 4. Phase 4 · 图像与视觉打磨（已完成）

- [x] SiliconFlow 图像 Provider：默认 `Tongyi-MAI/Z-Image-Turbo`，768×1024 / 512×512 / 1024×576 自动选择，SHA-256 缓存，失败不阻塞审核
- [x] IP 插画 `illustration` artifact：包装审核通过后生成；H5 故事区 + 包装工位展示；固定演示码提交 Z-Image-Turbo 快照
- [x] 包装视觉变体（经典牛皮纸/山野红/夜绿）；3D 相机阻尼
- [x] 空态/错误态/加载态；1280×720 短时采样 120fps；DPR 上限 2（长时压测留 Phase 5）
- [x] 七类丑自检逐项记录 pass/fixed/known-gap（H5 + 沙盘，见 ui.md §6）
- [x] 代码分割：index 260KB / Sandbox 37KB / Trace 23KB / Scene 950KB 异步 chunk

**Phase 4 验收**：真实 API 512×512 与 768×1024 均 200；Provider 类 768×1024 约 986KB、缓存命中；固定演示 H5 与包装工位显示插画；3 个包装变体可切换且 3D 贴图同步；1280×720 场景 2.5 秒采样 120fps；`SceneBoundary`/Suspense/API 重试/空批次新建已接；路由与 three.js 分包；43 后端测试、ruff、前端 typecheck/lint/build 全绿。长时 60fps、200% zoom 留 Phase 5。

## 5. Phase 5 · 加固与交付（已完成）

- [x] Playwright 冒烟：桌面 4 条（固定演示批次、包装变体/插画、插画失败视觉兜底、3D 二维码打开 H5）+ 移动 3 条（390px H5/扫码、320px 无溢出、未知码/超长码 404）
- [x] `POST /api/demo/reset` 幂等：重复 reset 不产生重复 run/artifact；扫码后 reset 归零；固定码 `ZTDEMO26` 不变
- [x] 第二产品档案夹具：麻江蓝莓，只建数据；mock 四站与真实 V4.1-Flash 四站都跑到 `traced`，`MJ` 溯源码，公开 H5/包装 PNG 可用，真实运行无 fallback、输出无昭通/苹果残留
- [x] LLM 未知字段忽略（#64）：真实营销输出多一个 `wechat.title_note: null` 不再整站降级；已知字段仍严格校验
- [x] 档案化输出：系统提示、Agent brief、mock 文案、定价标签/欢迎语/FAQ、包装品牌字、溯源码前缀均从 `ProductProfile.specs` 读取
- [x] 长时性能：60 秒采样 58.3fps，JSHeap 44.5MB→42.4MB；200% 等效视口回退桌面提示且无溢出
- [x] 一键启动：根 `Makefile` 的 `make dev/test/e2e/perf`；Playwright `webServer` 自动拉起未启动的服务
- [x] 来源补证：农业部公告第1478号/AGI2010-07-00370 入 GI-01；80–85mm 补 4 个惠农网公开挂牌页；包装厂 1000 个起订线索已记，无书面报价
- [x] 生图失败视觉兜底（包装工位）与缓存清理命令（30 天/512MB，支持 dry-run）
- [x] 局域网扫码入口：`make lan` 自动取 IP、Vite 监听 0.0.0.0、后端 `PUBLIC_BASE_URL` 与二维码指向局域网，reset 后可用；真机扫描仍需同一 Wi-Fi 实测
- [x] 文档收口：decisions #61–#67、`docs/v2/runbook.md`、AGENTS/README/plan/ui/sources
- [x] 字段级审核表单：Phase 5 确认不做，保留 JSON 编辑器（#58/#63）
- [x] Docker：确认不做，继续 uv + pnpm 本地进程（#63）
- [x] 演示脚本与彩排：见 `docs/v2/runbook.md` §4

**Phase 5 验收**：`pnpm test:e2e` 7 passed；`PERF_SECONDS=60 pnpm test:perf` 2 passed；后端 47 passed + 1 skipped（真实 LLM 默认跳过）、ruff、前端 typecheck/lint/build 全绿；`test_second_product_runs_without_code_changes` 与 `RSM_REAL_LLM=1` 真实四站均通过；`ZTDEMO26` 与 156% 溢价回归不变。

## 5.1 Phase 6 · 多产品 + 总控（已完成）

- [x] 知识库唯一约束改为 `(product_id, doc_key)`；两个产品可复用 `ORIGIN-01`
- [x] 产品下拉 + 批次按产品过滤；批次码前缀读 `specs.batch_prefix`
- [x] H5 标题/旅程从 `specs.trace_headline`/`product.name` 读取，不再写死昭通
- [x] 总控会话/消息持久化；PydanticAI 工具循环；动作白名单
- [x] 建档/通过/驳回/回退确认卡；早期站回退作废下游 Artifact
- [x] Firecrawl Provider + 逐字引用校验；无 key 提示贴资料
- [x] 右栏总控抽屉 + `/controller` 独立页；9 条 Playwright
- [x] 后端 52 passed + 2 skipped；迁移在全新 SQLite 通过
- [x] 真实 Firecrawl 搜索/抓页 + 麻江蓝莓草案（本机 key；1 条来源、价格缺失转追问）
- [ ] 真实手机扫码、包装厂书面报价、真实盒型/刀版

## 6. 未验证假设（开工即验证）

- [x] 真实 LLM key 可用；空 key mock 路径已跑通
- [x] 营销长文需要比 90s 更长的超时；已改 180s
- [x] V4.1-Flash 全链路可用：营销/定价也不再超时或数字不一致
- [x] 固定演示码 reset 后仍有完整内容（seed 快照 + 4 run/artifact）
- [x] H5 390px/320px 无横向溢出；二维码按钮可打开 H5
- [x] SiliconFlow 图像模型可用：`Tongyi-MAI/Z-Image-Turbo` 512×512/768×1024 均 200，约 ¥0.1/张；默认保留“AI 生成”水印
- [x] 3D 场景长时 60fps：headless Chromium 1280×720 采样 60 秒 58.3fps，堆内存不增长
- [x] 局域网扫码入口：`make lan` 已验 LAN 首页/H5/二维码 200，二维码 payload 指向局域网 IP
- [ ] 手机真机扫码（当前只验了 390px 视口、Playwright 移动模拟与局域网 HTTP，尚未用真实手机扫）
- [x] 200% 等效视口：640×360 回退桌面提示且无横向溢出；H5 320px/超长码已压测
- [x] 第二产品档案：麻江蓝莓夹具跑通 mock 四站与真实 V4.1-Flash 四站，不改核心代码
- [ ] 包装印刷成本/小批量报价（当前 5.7 元/盒为演示估算；只找到 1000 个起订线索）
- [x] 80–85mm 精选果公开挂牌价：惠农网 4 个页面（5斤 25/36/40 元，10斤 6.2 元/斤）；成交价/同渠道长期价仍待跟
- [x] 地理标志公告原文/公告号：农业部公告第1478号，AGI2010-07-00370（商务部政策法规库转录）

## 7. 已知缺口（Phase 6 结束时的诚实清单）

- 字段级审核表单**不做**（#63），保留 JSON 编辑器；盒型仍是单一视觉示意，不是真实刀版。
- 真实图像只生成 IP 插画；包装变体仅色板，不含真实盒型/刀版。生图失败已有视觉兜底，缓存清理用 `maintenance image-cache` 手动执行。
- 定价 156% 与包装成本 5.7 元/盒是演示测算；页面已标“演示测算”。
- 故事/内容里的区域事实已尽量引用知识库，但 LLM 仍可能写未引用的概括（FactGuard 对未引用数字只给 warning）；审核时看引用与预警。
- IP 对话只做了关键词/规则 + LLM 后置校验；没有多轮上下文管理、没有真人客服兜底。
- 第二产品真实 LLM 只跑了一次（四站无 fallback），未做多批次稳定性；提示词已档案化。
- 真实 Firecrawl 搜索/抓页已验；调研草案只拿到 1 条来源，价格/包装仍会转追问，需用户补资料。
- 总控 PydanticAI 工具循环实测比原计划多轮，默认限额调到 10 请求/12 工具；仍需真实调研观察费用与稳定性。
- 多产品 UI 已做，但不做多产品并列 3D；产品知识库/批次互相独立。
- 手机真机扫码、包装厂书面报价/食品接触合规、真实盒型/刀版仍未补齐；80–85mm 挂牌价与 GI 公告号已补，成交价仍待跟。
- Docker 不做；现场依赖本机 uv + pnpm + SQLite。
- 前端已分包：initial index 260KB、Scene 950KB 异步；手机 H5 不下载 three.js。
- v1 设计文档已移除；如需追溯见 git history（main 分支）。

## 8. 验收命令（当前）

```bash
# backend
cd backend
uv run alembic upgrade head
uv run python -m ruralsmartmark.seed
uv run pytest
RSM_REAL_LLM=1 uv run pytest tests/test_second_product_real.py   # 可选，会消耗额度
uv run ruff check .

# frontend
cd frontend
pnpm typecheck
pnpm lint
pnpm build

# 一键（仓库根）
make test
make e2e
make perf
```

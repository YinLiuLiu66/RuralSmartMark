# 总控与多产品 · 设计契约

> 状态：已批准，已完成（2026-10-22；2026-11-13 改为全局单会话 + 页面上下文）
> 决策：`docs/decisions.md` #68–#78，#92
> 目标：用户只面对一个输入框，完成“调研建档 → 四站流水线 → 修改/通过/回退”。

## 1. 角色

「总控」是控制面，不是第五个内容 Agent。四个 Agent 仍由现有 `orchestrator.py` 驱动，一次生成一站结构化产出。

总控可以：
- 读取所有产品、批次、`AgentRun`、`Artifact`、知识库；
- 调 Firecrawl 搜索/抓页，或向用户索取资料；
- 生成产品档案草案并提交；
- 调用 `run_agent(agent, note)`、`approve_agent`、`reject_agent`、`rewind`；
- 把结果、缺口、确认项汇总回同一对话。

总控不能：
- 直接改数据库、文件或发任意 HTTP；
- 未确认就建档、通过、驳回或回退；
- 把没有来源的内容标成事实。

## 2. 交互

- **全局唯一会话**：总控只有一段对话，跨页面连续；`POST /api/controller/sessions` 是 get-or-create，`product_slug/batch_id/fresh` 已废弃并被忽略。App 级 `ControllerDock` 在所有页面复用同一实例，`/controller` 只渲染全页版，不重复挂载。
- **页面上下文**：每条消息带 `{route, product_slug, batch_id, focus_agent}`；服务端校验产品/批次存在且归属一致，非法返回中文 400。上下文写入 user 消息 `action_json`，历史回放时前缀 `【页面：产品名 / 批次码】`。
- **写操作只认页面批次**：`run_agent`、`request_action` 不接收任何批次参数；页面没有批次时返回 `needs_target` + 候选，由模型反问、前端出候选 chip（点击跳转 `/project/:slug?batch=`）。
- **目标冻结**：`request_action` 出卡时把 `product_id/batch_id/batch_code/batch_state/batch_updated_at/draft_sha256` 写进 pending；确认阶段只从 pending 取目标与草案，状态或草案哈希变化即中文 409 拒绝。
- **并发**：单把全局锁覆盖「一轮对话」与「一次确认」，冲突 fail-fast 409，不排队。
- 用户消息发送后立即显示（服务端落库后回填真实 id），不等整轮结束。
- 回复走 SSE 流式：正文按 token 增长；`reasoning_content` 显示为「思考过程」，默认折叠，展开后一行一条。
- 工具执行期间显示中文状态（检索、抓页、调用 Agent、准备确认卡）。
- 对话里的确认卡负责危险动作，卡上显示目标批次；普通消息不弹窗。
- 运行流水线的节奏：你说“开始运行”，总控跑当前站并汇报；你说“审核通过”，总控生成确认卡；确认后后端通过并自动运行下一站，下一站仍停在待审核。
- 没有页面上下文时（如 `/controller` 或工作台），写操作一律反问并给候选，不默认落到“最近批次”。

示例：
- “我想做贵州麻江蓝莓，帮我查产地和价格。”
- “包装太红，改克制一点。”
- “通过故事。”
- “回到包装重做。”
- “我有哪些项目？”（只读，不需要目标）

## 3. 动作白名单

### 读取/调研（直接执行）
`list_products`、`list_batches`、`get_workspace`、`research_product`、`record_inputs`。

`get_workspace` / `list_batches` 可显式传 `product_slug` / `batch_code` 做**只读**查看；读到的批次不等于写目标。


### 执行（用户明确要求时）
`run_agent(agent, note)`。

### 必须确认
`commit_product`、`create_batch`、`approve_agent`、`reject_agent`、`rewind_to_agent`、`delete_batch`。`request_action` 的 kind 必须逐字使用这六个值；模型提示词里点名“建档用 `commit_product`”，不要发明 `start_batch` / `create_product` 等名字。

确认由后端生成 `pending_action_json`，`confirm` 接口执行；模型不直接执行危险动作。`approve_agent` 确认通过后自动启动下一站并停在待审核；定价通过后直接进入 `traced`。每站仍需用户再次确认，不做连续自动通过。

`delete_batch`（decisions #87/#92）只删确认卡冻结的那个批次，不接受跨批次指定；`ZT-DEMO-001` 与仍有活跃 run 的批次在服务层拒绝（409，run 超过 10 分钟视为崩溃遗留可放行），错误以中文说明返回、由模型转述。删除时先清 `backend/data/artifacts/` 产物文件，再借外键级联清运行/产物/扫码/H5 对话记录；执行后 `ControllerSession.batch_id` 置空（仅作「最近操作」展示）。

`create_batch`（decisions #88/#92）只给确认卡冻结的产品开批次，可带 `quantity_kg`（默认 300）；确认后创建下一编号批次（前缀读 `specs.batch_prefix`），前端据返回的 `session.batch_id` 跳转到新批次。创建与编号逻辑在 `services/batch_create.py`，与 `POST /api/batches` 共用；顶栏「新建批次」按钮（decisions #86）仍是手动入口。

## 4. 限额

使用 PydanticAI `UsageLimits`；可配置：

```env
CONTROLLER_REQUEST_LIMIT=10
CONTROLLER_TOOL_CALLS_LIMIT=12
RESEARCH_REQUEST_LIMIT=10
RESEARCH_TOOL_CALLS_LIMIT=16
```

- `request_limit` 计模型轮数；`tool_calls_limit` 计工具执行次数。
- 搜索一次返回最多 5 条；抓取一次最多 4 页；批量算一次工具。
- 超限返回当前草案与“继续”，不丢数据。
- 这些是延迟/费用/防循环保护，不是业务常数。实测 4/8 对 PydanticAI 的“工具调用 + 最终结果”不够；控制器调到 10/12，研究 Agent 调到 10/16，并对搜索 3 次/抓取 4 页做显式封顶；仍可配置，超限返回中间结果。

## 4.1 上下文与压缩（decisions #89）

每轮请求是真多轮 messages，不是把历史压成一段文本：

```
[system]   CONTROLLER_INSTRUCTIONS（永远在最前，逐字节稳定）
[user]     【对话压缩档案】……（仅有压缩历史时出现，≤800 字）
[user]/[assistant]  压缩点之后的原始消息，逐条映射
[user]     【当前上下文】JSON 快照 + 本轮用户消息   ← 易变内容只在最后一条
```

- 不再用 `-12` 硬窗口；历史长度由压缩机制管。前缀稳定是为了吃满硅基流动的前缀缓存。
- 发送前估算 token（CJK≈0.7/字、其余≈0.28/字符）；达到 `CONTROLLER_CONTEXT_TOKENS × CONTROLLER_COMPRESS_RATIO`（默认 1024000×0.8）时调用 `LLM_COMPRESS_MODEL`（默认 `XingChenAGI/Xing4.0-29B`，复用 `OPENAI_BASE_URL`/`OPENAI_API_KEY`）把「既有摘要 + 未压消息」压成交接档案。
- 档案必须保留：任务目标与最新意图、绑定产品/批次与流水线状态、已执行动作与确认结论、用户偏好与禁令、未决问题。
- 摘要存 `controller_session.summary_json = {text, upto_message_id}`；`ControllerMessage` 原始消息**永不删除**（审计与历史回看依赖它）。加载历史 = 摘要 + `upto_message_id` 之后的真实消息。
- 压缩失败不阻塞对话：本轮退化为丢弃最旧一半历史（不入库），下一轮重试；用户无感知，仅体现为该轮等待变长，后端日志记一行。
- 四站流水线 Agent 是单轮全量（system + 知识库 + 上游产出），量级远低于阈值，不走压缩。

## 5. 数据模型

### `knowledge_doc`
- `doc_key` 从全局唯一改为 `(product_id, doc_key)` 复合唯一；多产品可复用 `ORIGIN-01`。
- `upsert_knowledge_docs` 按 `product_id + doc_key` 查找。

### `controller_session`
`id / product_id? / batch_id? / draft_json / pending_action_json / summary_json / created_at / updated_at`。
- **全局单行**：唯一索引 `uq_controller_session_single`（`ON controller_session ((1))`）。迁移 `f18a3c5e7b90` 删除全部旧会话与消息后重建。
- `product_id/batch_id` 降级为「最近操作」展示缓存，不再作为任何写操作的默认目标。

### `controller_page_context`（非表，消息体字段与消息内快照）
`route / product_slug / batch_id / focus_agent`；写入 user 消息 `action_json = {page_context, page_label}`。

### `controller_message`
`id / session_id / role / content / action_json / created_at`。

不新增 Agent 间消息表。Agent 的“消息”是 `AgentRun.note/error/output_json`；总控读取并转述。

## 6. 调研与来源

- Provider：Firecrawl `AsyncFirecrawl`（后端 venv）；适配层默认绕过系统代理（`FIRECRAWL_TRUST_ENV=false`），避免本地代理导致长连接 EOF。
- 网络类失败自动重试一次（叠加 SDK 自身重试），仍失败时返回中文提示：稍后再试或直接贴来源链接/原文；401/403 不重试。
- 每次调研：生成 2–3 个查询 → 搜索 → 批量抓页 → 提取候选事实。
- `ResearchDraft`：product/specs/palette/docs/benchmarks/questions/sources/warnings。
- 每个 `quote` 必须在抓取 Markdown 中逐字出现；否则丢弃并提示。
- 缺品牌/IP、包装规格、三档价格时追问，不硬凑。
- 自动生成 `DEMO-01`（所有价格/成本/溢价均为演示测算）与 `PRICE-01`（演示测算采用…）。
- 只存 URL、标题、检索日期、短引用，不整页转载。

## 7. 回退

- 当前待审核站：`run(note)`，不影响下游。
- 已通过且下游存在：确认后清空下游 `batch.*_json`、删除下游 Artifact/插画文件、下游 run 标记 failed（error=`rewound by controller`），批次回到目标站可运行状态，再 `run(target, note)`。
- 历史 `AgentRun` 保留作审计；确认卡必须说明“后续内容/定价会作废重跑”。

## 8. API

- `POST /api/controller/sessions`：**get-or-create 全局唯一会话**，请求体可为空；`product_slug/batch_id/fresh` 已废弃并被忽略，不要再依赖返回值里的绑定关系判断“当前页面”。
- `GET /api/controller/sessions/{id}`：消息、草案、pending action；同时返回 `product_name/batch_code/batch_state`（最近操作，仅展示）。窗口聚焦时重拉。
- `POST /api/controller/sessions/{id}/messages`：非流式发送；请求体 `{message, context?}`，`context` 为 `{route, product_slug, batch_id, focus_agent}`。
- `POST /api/controller/sessions/{id}/messages/stream`：SSE 流式，事件 `user` → `thinking`/`delta`/`tool` → `done`；失败发 `error`。`done.turn.needs_target` 在缺目标时携带候选。
- `POST /api/controller/sessions/{id}/confirm`：`{action_id, decision}`；执行前先清空 pending（防重复点击），目标一律来自 pending 冻结值。

所有写操作复用现有 `run_agent/approve_agent/reject_agent`。SSE worker 使用独立数据库会话，客户端断开时取消本轮模型调用；已落库的用户消息保留。

## 9. 安全

- Firecrawl 只接收 query/URL；key 只在 `backend/.env`。
- LLM 不能拼 SQL/文件路径/任意请求；所有动作走白名单。
- 建档/开批次/通过/驳回/回退/删除批次二次确认；确认卡显示冻结目标，目标状态或草案变化即拒绝执行。
- 模型不能指定批次 id：写工具只接受动作与站点，目标由服务端从页面上下文解析。
- 知识条目必须有 `source_url`、检索日期、credibility；无来源只能 `todo/demo`。
- 真实人物/认证/功效/保证红线不变。

## 10. 验收

- 两个产品可复用同一 `doc_key`；切换产品批次正确。
- 从 UI 能完成：新建空白会话 → 调研 → 草案 → 确认建档 → 跑故事 → 对话修改 → 通过 → 回退。
- 发消息后用户气泡立即出现；思维链默认折叠、可展开；正文流式出现。
- 无 Firecrawl key 时提示贴资料，不静默失败；网络失败提示可重试/贴链接。
- 后端 106 passed + 2 skipped，Playwright 13 条，构建通过；真实 Firecrawl 小样本可选通过。

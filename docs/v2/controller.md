# 总控与多产品 · 设计契约

> 状态：已批准，实施中（2026-10-22）
> 决策：`docs/decisions.md` #68–#71
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

- 桌面沙盘右栏 Tab：「站点 / 总控」；顶栏「总控」打开抽屉。
- `/controller` 是同一面板的独立路由，供窄屏或直达使用。
- 首次没有产品时，直接打开「新建产品」对话。
- 对话里的确认卡负责危险动作；普通消息不弹窗。

示例：
- “我想做贵州麻江蓝莓，帮我查产地和价格。”
- “包装太红，改克制一点。”
- “通过故事。”
- “回到包装重做。”
- “现在到哪了？”

## 3. 动作白名单

### 读取/调研（直接执行）
`list_products`、`select_product`、`list_batches`、`get_workspace`、`get_agent_output`、`get_knowledge`、`search_web`、`scrape_sources`、`update_draft`。

### 执行（用户明确要求时）
`run_agent(agent, note)`、`create_batch(product_slug, quantity_kg)`。

### 必须确认
`commit_product`、`approve_agent`、`reject_agent`、`rewind_to_agent`。

确认由后端生成 `pending_action_json`，`confirm` 接口执行；模型不直接执行危险动作。

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

## 5. 数据模型

### `knowledge_doc`
- `doc_key` 从全局唯一改为 `(product_id, doc_key)` 复合唯一；多产品可复用 `ORIGIN-01`。
- `upsert_knowledge_docs` 按 `product_id + doc_key` 查找。

### `controller_session`
`id / product_id? / batch_id? / draft_json / pending_action_json / created_at / updated_at`。

### `controller_message`
`id / session_id / role / content / action_json / created_at`。

不新增 Agent 间消息表。Agent 的“消息”是 `AgentRun.note/error/output_json`；总控读取并转述。

## 6. 调研与来源

- Provider：Firecrawl（`firecrawl` SDK，后端 venv）。
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

- `POST /api/controller/sessions`：创建/获取会话。
- `GET /api/controller/sessions/{id}`：消息、草案、pending action。
- `POST /api/controller/sessions/{id}/messages`：发消息，执行读取/调研/运行类动作。
- `POST /api/controller/sessions/{id}/confirm`：`{action_id, decision}` 执行/取消危险动作。

所有写操作复用现有 `run_agent/approve_agent/reject_agent`。

## 9. 安全

- Firecrawl 只接收 query/URL；key 只在 `backend/.env`。
- LLM 不能拼 SQL/文件路径/任意请求；所有动作走白名单。
- 建档/通过/驳回/回退二次确认。
- 知识条目必须有 `source_url`、检索日期、credibility；无来源只能 `todo/demo`。
- 真实人物/认证/功效/保证红线不变。

## 10. 验收

- 两个产品可复用同一 `doc_key`；切换产品批次正确。
- 从 UI 能完成：新建产品 → 调研 → 草案 → 确认建档 → 跑故事 → 对话修改 → 通过 → 回退。
- 无 Firecrawl key 时提示贴资料，不静默失败。
- 后端测试、Playwright、构建全绿；真实 Firecrawl 小样本可选通过。

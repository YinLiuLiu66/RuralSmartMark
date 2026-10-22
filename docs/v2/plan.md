# 乡土印记 v2 · 重写方案

> 状态：方案已确认，待实施  
> 日期：2026-10-21  
> 首个案例：昭通丑苹果（云南省昭通市昭阳区）  
> 范围：单案例深做 + 可复制架构  
> 说明：本文是产品与技术方案，不是最终代码；架构决策在 Phase 0 统一落 `docs/decisions.md`（#32 起）。  
> 重写原则：greenfield。旧后端/前端代码、旧 CSS token、旧文档约定只作历史参考，不作为实现约束；可复用的是外部参考（WareTrack）与公开事实。

## 0. 定案摘要

- **首个案例**：昭通丑苹果（云南省昭通市昭阳区），虚构合作社子品牌，5kg/12 枚礼盒。
- **产品形态**：3D 县域品牌流水线沙盘 + 四 Agent 上下文工作台 + 移动端溯源 H5。
- **技术栈**：React + TypeScript + Vite + React Three Fiber + Zustand + Tailwind；FastAPI + SQLAlchemy 2.0 + SQLite；SSE；LLM/图像 Provider 可插拔。
- **范围**：单案例深做；核心产品无关；不做游戏化；不做多产品 UI；单用户免登录。
- **原则**：先用 mock 打通端到端，再接真实模型；每个 Agent 都有人工审核门；所有事实带出处，演示数字标注口径。

### 为什么是昭通丑苹果

1. 故事钩子强："丑"是天然反差；高海拔、日照长、昼夜温差大、冰糖心（不是每颗都有）是可引用的事实/现象；“不套袋、不打蜡”只作为演示合作社设定，并引用 DEMO-01。
2. 视觉辨识度高：红果、绿园、牛皮纸礼盒；低多边形场景容易出效果。
3. 溢价链条清楚：演示基线散装 5 元/斤（10 元/kg）vs 品牌礼盒目标 25.6 元/kg；"地头价 → 礼盒价"的对比直观，但必须标“演示测算”。
4. 公开资料足够：国家地理标志、昭阳区核心产区、品质指标、2024 年产业规模都有可引用来源；具体海拔数字未核到官方原文，改用“高海拔”定性表述。
5. 叙事空间大：乌蒙山、近百年引种培育；彝族纹样/昭通古城等文化素材在核到与产区的直接关联前不进入故事。

**边界**：昭通苹果是区域公用品牌，已有知名度。项目不冒充区域品牌，而是做一个**虚构合作社的子品牌**（例如"乌蒙丑果"），讲"区域品牌有了，合作社和农户仍按斤卖，AI 帮他们做子品牌和礼盒溢价"。既真实，又不抢区域品牌的功劳。

**数据口径**：第一轮核验后，知识库采用“高海拔、低纬度、日照长、昼夜温差大”的定性表述（具体海拔数字未核到官方原文，不写 1950m）；品质指标用地理标志登记资料的可溶性固形物≥15.0%、含糖量≥13.0%；2024 年产业数据用云南日报报道。价格与包装成本按演示测算，逐条来源见 `sources.md`；页面标注“演示测算”。

**备选**：麻江蓝莓只做第二个 `ProductProfile` 测试夹具，证明换产品不改核心代码；不做 UI、不做第二套 3D 场景。虚构县不推荐，竞赛需要可查证的真实性。

---

## 1. 产品定位

一句话：**让一个县域农产品批次，从地头价走到品牌价——四个 AI Agent 在 3D 沙盘上完成故事、包装、内容、定价与溯源。**

- 用户：县域合作社/农业品牌主理人；消费者（扫码看溯源）。
- 价值：把数万元的设计、策划、定价能力，变成一条可复制的流水线；AI 出 80% 初稿，人做 20% 判断与润色。
- 不是什么：不是 WMS，不是经营游戏，不是四个孤立的聊天窗口。

---

## 2. 核心叙事与动线

一个批次 `ZT-2026-001` 的旅程：

1. **原料入库**：果园/合作社，苹果批次、产地、采摘日期、糖度、数量。
2. **故事馆（Agent 1）**：知识库 + 果农口述 → IP 定位、品牌故事、标签、引用证据。
3. **包装工坊（Agent 2）**：故事 → IP 形象、包装文案、结构/成本、3D 盒贴图。
4. **内容工坊（Agent 3）**：故事 + 包装 → 小红书/抖音/朋友圈、客服 Q&A、KOL Brief。
5. **云仓/门店（Agent 4）**：成本 + 竞品 → 价格梯、溢价率、二维码、溯源时间线。
6. **消费者扫码**：H5 打开，IP 人格讲这批苹果的旅程，可对话。

每一步都有 `待审核` 门：运营者可以改文案、换方案、写一句"更乡土一点"重跑；通过后批次才进入下一站。底部"品牌护照"stepper 记录六步状态；3D 场景里的批次、包装、广告牌、卡车、二维码随状态变化。

**高光时刻**（产品自然产生，不是硬编码演出）：

- 包装工坊完成后，3D 里的箱子从牛皮纸毛坯变成带 IP 和文案的礼盒。
- 内容工坊完成后，场景里的广告牌/直播屏亮起生成的小红书封面。
- 定价完成后，礼盒上出现二维码；点"模拟扫码"，手机框里打开溯源页。
- 溢价 KPI 从 0 跳到 150%+，旁边标注"演示测算"。

---

## 3. 信息架构

### 页面

- `/` 沙盘主页面（桌面优先，1280×720 起）。
- `/batch/:id` 品牌护照全页（深读/编辑四章产出物）。
- `/trace/:code` 消费者溯源 H5（移动优先，390px 起）。
- 无独立 workbench；右侧上下文卡就是轻工作台，"展开"进入 `/batch/:id`。

### 沙盘布局

- 顶栏：Logo「乡土印记」、产品/批次切换、流水线状态 pill、主按钮「运行流水线」、通知、设置。
- 左侧：4–5 张 KPI 卡（品牌溢价率、故事定稿、包装方案、内容素材、扫码次数）。
- 中央：等距 3D 场景（果园、故事馆、包装工坊、内容工坊、云仓/门店、道路、卡车、批次托盘）。
- 右侧：上下文详情卡（站点/批次/门店/卡车）。
- 左下：品牌护照 stepper（原料 → 故事 → 包装 → 内容 → 定价 → 溯源）。
- 右下：产出物 Tab（故事/包装/内容/定价/溯源）。
- 左中：相机控件（放大/缩小/左转/右转/复位）。
- 空态/加载/错误：骨架屏、重试按钮、SSE 断线提示。

### 交互

- 点站点：右卡显示 Agent 状态、输入摘要、产出预览、运行/重跑/审核、日志。
- 点批次：右卡显示品牌护照摘要；"展开"进入全页。
- 点门店/二维码：右卡显示扫码次数、打开溯源页、模拟扫码。
- 相机：拖拽平移、滚轮/双指缩放、旋转按钮每次 45°、复位缓动；轨道限制在等距范围。
- 审核弹窗：可编辑文本、选择变体、写重跑备注；通过/驳回；记录审核时间。
- 重跑：接受一句自然语言备注（"更年轻""更贵气""少用形容词"），作为 Agent 输入。
- 重置：设置里"重置演示数据"，回到 seed 状态。

### 视觉语言

- 关键词：山野编辑部、暖、克制、有纸张感；不是 WMS 冷色控制塔。
- 色板：米白底 `#F7F3EA`、墨绿 `#1F3A2E`、苹果红 `#C8452D`、叶绿 `#4F7A5A`、牛皮纸 `#C9A46A`。
- 字体：PNG 用内置 Noto Serif SC / Noto Sans SC（OFL）；SVG 保留字体栈；数字用 tabular；不依赖外部字体 CDN。
- 卡片：16–20px 圆角、细边框、柔和阴影；不用重玻璃拟态。
- 3D：低多边形、暖阳光、软阴影；建筑带一点乡村屋檐/木构意象，不做写实仓库。
- 动效：站点状态点、批次沿路移动、数字 count-up、产出物翻页；不做游戏化弹窗/彩带。

---

## 4. 四个 Agent

### 4.1 共享契约

- 每个 Agent 一次运行 = `AgentRun`：`queued/running/waiting_review/approved/failed`。
- 输出必须是 Pydantic 校验过的 JSON；原始输出、解析结果、token、模型、错误都入库。
- 输入 = 产品档案 + 已通过的上游产出 + 知识库片段（带 doc_id）+ 约束 + 输出 schema。
- 事实规则：涉及产地、年份、认证、价格、糖度、人物的陈述必须带 `doc_id` 或标记为"创作"；后端 `FactGuard` 校验，未通过则重试/阻断。
- 人工审核门：默认每个 Agent 完成后暂停；开发可开 `AUTO_APPROVE=true`，但审核记录仍保留。
- 失败策略：校验失败自动重试 1 次（带错误信息修复 prompt）；仍失败则标记 failed，保留已有产出，不阻塞沙盘。

### 4.2 Agent 1 · 乡土故事挖掘机

- 输入：产品档案、知识库（地理标志/产区/种植/文化/口述/价格）、果农口述（文本或可选音频转写）、目标人群。
- 输出 JSON：`ip_name`、`persona`（性格/说话方式/禁忌）、`story_long`（500–800 字）、`story_short`（120 字）、`taglines[]`、`cultural_evidence[{doc_id, quote, use}]`、`tone_guide`。
- 工具：知识检索（20 篇以内全量 + BM25，不引向量库）、可选 ASR Provider、LLM。
- 校验：引用存在；不出现知识库外的人名/年份/认证；故事必须包含产品事实（产地、种植方式、口感）。
- UI：故事卡、引用 chips、口述波形（有音频时）、可编辑字段。

### 4.3 Agent 2 · 包装设计智能体

- 输入：已通过的故事/IP、产品规格（5kg/12 枚/80–85mm/保鲜要求）、包装模板、品牌色。
- 输出 JSON：`concept`、`palette`、`typography`、`ip_image_prompt`、`packaging_copy{front,back,side,inside}`、`structure{box_type,dimensions,material}`、`cost_estimate`、`derivative_ideas[]`。
- 工具：图像 Provider（真实/mock）、Pillow 合成器 + 内置字体、SVG 导出、模板注册表。
- 校验：文案长度适配版面；二维码占位；不出现"有机/绿色食品"等未认证标志；成本算术正确。
- UI：正面/背面/侧面/盒型预览、变体画廊、3D 盒贴图、导出 PNG/SVG（标注"示意"）。

### 4.4 Agent 3 · 农产品营销官

- 输入：故事、包装、产品、目标渠道、人群、KOL 库。
- 输出 JSON：`xiaohongshu{title,body,tags,cover_text}`、`douyin{hook,script,shots[]}`、`wechat{title,body}`、`cs_qa[{q,a}]`、`kol_brief{profile,rationale,message,deliverables[]}`。
- 工具：LLM、渠道模板、合规清单、KOL 数据集（本地）。
- 校验：无医疗/保健功效；无虚假稀缺；字数/标签数符合渠道；语气与 IP 一致。
- UI：手机框预览（小红书/抖音）、Tab 切换、一键复制、KOL 卡片。

### 4.5 Agent 4 · 溢价核算与溯源

- 输入：成本结构、竞品基准、包装成本、目标毛利、批次数据（果园/采摘/果农/检测）、故事/IP。
- 输出 JSON：`price_ladder[{channel,price,margin}]`、`premium_pct`、`rationale`、`trace_timeline[]`、`qr_payload`、`persona_greeting`、`faq[]`。
- 工具：确定性定价计算器、二维码生成、溯源数据、LLM（只写解释，不改数字）。
- 校验：服务端重算价格/毛利率/溢价公式；基准必须有 `source_url + date`；禁止"保证增收"类承诺。
- UI：价格梯表/条形图、溢价徽章（带公式 tooltip）、二维码、溯源预览。

### 4.6 编排器

- 状态机：`raw → story_running → story_review → story_approved → packaging_running → ... → priced → traced → shipped`。
- API：start/next/run/approve/reject/retry；同一批次只允许一个活跃 run（DB 锁/状态检查）。
- SSE：每次状态变化、日志、产出物就绪都推事件；前端断线重连后重新拉快照。
- 幂等：重复 start 不重复生成；approve 已通过则返回当前状态。

---

## 5. 3D 沙盘

### 场景

- 一块 48×36 的低多边形县域地块；果园在左上，故事馆在左中，包装工坊在中下，内容工坊在右中，云仓/门店在右下；一条环路串起来。
- 批次：托盘 + 纸箱；包装前是牛皮纸毛坯，包装后换成生成贴图的礼盒；沿 CatmullRom 曲线移动。
- 卡车：包装完成后从云仓出发，沿路开到门店；不参与复杂调度，只表达"出库"。
- 站点状态：idle 灰、running 主色发光点、waiting_review 琥珀、done 绿；Phase 1 用状态点 + 静态 emissive，呼吸光留 Phase 4。
- 广告牌/直播屏：内容工坊完成后显示生成的小红书封面/标题。
- 二维码：定价完成后出现在礼盒侧面/门店立牌；点击打开手机框预览。
- 果园：成排苹果树（instanced），可点选看产地/批次信息。

### 技术

- R3F + Drei：OrthographicCamera、OrbitControls（限制极角/距离）、RoundedBox、Outlines、Html、Instances。
- 选中：raycast + outline + floating label；点空白取消。
- 相机：拖拽平移、滚轮/双指缩放、旋转按钮 45°、复位缓动；默认等距 45°。
- 灯光：HemisphereLight + DirectionalLight（软阴影）+ 环境光；阴影贴图 1024；DPR 上限 2。
- 性能：目标 60fps @1280×720；树木/箱子 instancing；不在每帧 setState；事件驱动动画。
- 资产：全部程序化几何（Box/Cylinder/Cone/Sphere/Plane + MeshStandardMaterial + Texture），对齐 WareTrack 的构建方式；广告牌/二维码用 Html 覆盖层保证中文与二维码清晰；v2 不引 GLB/写实资产管线，也不搬 WareTrack 的模型/贴图。
- 代码复用：相机、raycast、标签定位等模式可参考/复用 WareTrack 的实现；在 `docs/v2/references.md` 标注出处。

---

## 6. 技术架构

### 仓库结构

```
backend/
  src/ruralsmartmark/
    main.py config.py db.py deps.py models.py schemas.py
    routes/ health.py products.py batches.py demo.py
    agents/ base.py
    providers/ llm.py image.py
    services/
    seed/ __init__.py __main__.py
  migrations/ versions/
  alembic.ini pyproject.toml
  tests/ conftest.py test_health.py test_seed.py test_batches.py
frontend/
  src/
    main.tsx App.tsx
    three/ Scene.tsx Ground.tsx Stations.tsx Batch.tsx Truck.tsx CameraRig.tsx Selection.tsx
    components/ TopBar.tsx KpiCards.tsx StationCard.tsx BatchCard.tsx BrandPassport.tsx ArtifactTabs.tsx ReviewModal.tsx PhonePreview.tsx CameraControls.tsx
    stores/ world.ts pipeline.ts
    api/ client.ts sse.ts
    routes/ Sandbox.tsx BatchDetail.tsx Trace.tsx
    styles/
  package.json vite.config.ts tsconfig.json
data/
  knowledge/zhaotong/*.md
  products/*.json
  seed/*.json
  artifacts/            # gitignored
docs/
  decisions.md          # v1 #1–#31 + v2 #32 起
  v2/ plan.md ui.md sources.md   # architecture/agents/data/runbook/references 按需补
  05-next-steps.md       # v2 当前进度与下一步
AGENTS.md README.md
```

### 前端

- React 19 + TypeScript + Vite；R3F + Drei；Zustand（world/pipeline 两个 store）；Tailwind CSS v4；原生 `<dialog>` 做审核弹窗，Radix 只用于 Tabs/Tooltip；lucide-react 图标。
- 数据：启动拉 `GET /api/products` + `GET /api/batches`；SSE 订阅批次事件；断线指数退避重连；重连后重拉快照。
- 路由：`/`、`/batch/:id`、`/trace/:code`；沙盘页不因 SSE 高频事件整页重渲染。
- 测试：`pnpm typecheck`、`pnpm lint`、`pnpm build`；Playwright 冒烟走一遍主流程。

### 后端

- FastAPI + Pydantic v2 + SQLAlchemy 2.0（async）+ aiosqlite；Alembic 迁移（同步 URL 跑迁移，应用用 async engine）。
- SSE：`sse-starlette`；单 worker + 内存事件总线（不引 Redis/Celery）。
- LLM：OpenAI SDK；环境变量 `OPENAI_API_KEY`/`OPENAI_BASE_URL`/`OPENAI_MODEL`；默认 SiliconFlow DeepSeek-V4.1-Flash（可改），推理预算 `thinking_budget=2048`、最终输出 `max_tokens=4096`；`MockLLMProvider` 无 key 可用。
- 图像：`ImageProvider` 接口；`SiliconFlowImageProvider`（模型可配，按 v2 Provider 接口重写）+ `MockImageProvider`（Pillow 生成图案/占位）；生成结果下载到本地，按 prompt hash 缓存。
- 包装合成：Pillow 服务端渲染；内置 Noto Serif SC / Noto Sans SC（OFL）；输出 1600×1000 印刷示意 PNG，SVG 渲染函数保留作后续导出。
- 二维码：`qrcode[pil]`；`PUBLIC_BASE_URL` 生成 `/t/{code}`。
- 配置：`.env`（LLM/图像/`DATABASE_URL`/`PUBLIC_BASE_URL`/`AUTO_APPROVE`）；`.env.example` 入库。
- 部署：开发时 `uv run ruralsmartmark` + `pnpm dev`；生产 `pnpm build` 后 FastAPI 挂 `frontend/dist`；可选 Dockerfile + compose（app 单服务，SQLite 卷）。

### 数据模型

| 表 | 关键字段 | 用途 |
|---|---|---|
| `product_profile` | slug, name, county, category, form, specs_json, palette_json, scene_preset, knowledge_dir | 产品档案；换产品不改代码 |
| `batch` | code, product_id, quantity_kg, state, current_station, story_json, packaging_json, marketing_json, pricing_json, trace_code | 批次与四章产出 |
| `agent_run` | batch_id, agent, status, input_json, output_json, model, tokens, error, started_at, finished_at | 运行记录/审计 |
| `artifact` | batch_id, agent_run_id, kind, content_json, file_path, approved_at | 产出物与文件 |
| `knowledge_doc` | product_id, title, type, source_url, source_date, content, credibility | 知识库/引用 |
| `benchmark` | product_id, channel, competitor, spec, price_per_kg, source_url, source_date | 价格基准 |
| `kol` | name, platform, followers, tags, region, rate, note | KOL 匹配 |
| `scan_event` | batch_id, trace_code, created_at, channel, user_agent | 扫码统计 |
| `chat_message` | batch_id, role, content, created_at | 溯源页对话 |

### API

- `GET /api/products`、`GET /api/products/{slug}`
- `POST /api/batches`、`GET /api/batches`、`GET /api/batches/{id}`
- `GET /api/batches/{id}/workspace`（batch + runs + artifacts）
- `POST /api/batches/{id}/pipeline/start`
- `POST /api/batches/{id}/agents/{agent}/run`（body: note）
- `POST /api/batches/{id}/agents/{agent}/approve`（body: edited output）
- `POST /api/batches/{id}/agents/{agent}/reject`（body: note）
- `GET /api/batches/{id}/events`（SSE）
- `GET /api/trace/{code}`、`GET /api/trace/{code}/packaging.png`、`GET /api/trace/{code}/qr.png`
- `GET|POST /api/trace/{code}/scan`、`POST /api/trace/{code}/chat`（公开只读 + 对话边界）
- `GET /api/benchmarks?product_id=`
- `POST /api/demo/reset`、`GET /api/health`

### SSE 事件

Phase 1 实现：`batch.updated`、`agent.started`、`agent.completed`、`agent.failed`、`artifact.ready`；Phase 3 增加 `trace.scanned`（带 `scan_count`）。`sse-starlette` ping 保活；`agent.log`、`pricing.updated` 仍未做。事件带 `id`；前端重连后重新拉 workspace 快照。

---

## 7. 可复制架构

- 四个可替换件：`ProductProfile`、`KnowledgeDoc` 集、`PackagingTemplate`、`BenchmarkSet`；3D 场景有 `scene_preset`（果园/茶园/稻田/大棚）和产品 mesh 预设。
- 换产品 = 新档案 + 知识库 + 包装模板 + 基准价 + 场景预设；Agent 代码、编排器、审核流、溯源 H5、沙盘骨架都不改。
- 用麻江蓝莓做**第二个档案的测试夹具**：只建数据，不建第二套 3D/UI；pytest 用 mock LLM 跑完整流水线，证明"换档案不改代码"。
- 文档写一页《如何新增一个产品》清单；这是答辩时"可复制"的证据。

---

## 8. 知识库与事实边界

- `data/knowledge/zhaotong/` 10–15 篇 Markdown，frontmatter：`id/title/type/source_url/source_date/credibility`；type = GI / 产区 / 种植 / 文化 / 口述 / 价格 / 包装 / 检测。
- 检索：当前 10 篇全量注入（带 doc_id/来源）；规模上来后再加 BM25 选段，不引向量数据库。
- 口述：写一段"演示合成"的果农口述，明确标注"非真实人物"；只借用无人称语感，不编造姓名/亲历/年限。
- 价格：每条基准带 URL + 检索日期；页面和 API 都返回 `is_demo=true` 与公式；禁止"保证增收"。
- 认证：只用"昭通苹果国家地理标志"等可查事实；"有机/绿色食品"未认证不写。
- `FactGuard`：正则抽年份/百分比/认证/人名 + 引用校验；不通过的 claim 在 UI 标黄，阻断进入下一站；重跑时把违规点写进 prompt。
- `docs/v2/sources.md` 汇总所有来源；实现前逐条核验，冲突数据用区间并注明。

---

## 9. 实施顺序（按依赖，不按周）

### Phase 0 · 地基

Phase 0 在 `rewrite/v2` 开发，后并入 `main`；新文档与决策；backend/frontend 脚手架；SQLite/Alembic；seed（产品档案、知识库、基准价、一个 raw 批次、一个已完成演示批次）；mock LLM/Image Provider；健康检查。

**验收**：`uv run pytest`、`pnpm typecheck/lint/build` 全绿；打开页面能看到 seed 批次。

### Phase 1 · Walking skeleton（全 mock）

静态沙盘 + UI 壳；点击站点/批次；mock 流水线 start → 四个 mock 产出 → 审核 → 批次移动；SSE；品牌护照 stepper；溯源页 mock；二维码。

**验收**：不配任何 key，点"运行流水线"能走完六步；刷新/重连状态不丢。

### Phase 2 · 真实 Agent

Agent 1–4 接真实 LLM；知识库与 FactGuard；包装合成器；结构化输出校验/重试；人工审核编辑；重跑备注。

**验收**：每个 Agent 产出通过 schema；引用可点；违规 claim 被拦截；pytest 覆盖三态流转。

**实现口径**：10 篇知识库 Markdown；Pydantic 输出模型 + 重试 1 次 + mock 降级；FactGuard 逐字引用/违禁词/数字预警；定价确定性计算器 + 服务端重算；内置 Noto 字体 + 服务端 PNG 预览；审核 UI 保留 JSON 编辑器并加引用/预警/包装预览（字段级表单仍未做，见 decisions #51/#58）。

### Phase 3 · 沙盘联动

批次路径/站点状态/包装贴图/广告牌/二维码全部接真实状态；KPI 与 SSE；溯源 H5 + IP 对话；产出物 Tab；手机框预览。

**验收**：真实流水线走完后，沙盘与 H5 内容一致；390px 手机视口可用。

**实现口径**：公开 `GET /api/trace/{code}` 聚合批次/产品/四章产出/引用/价格/时间线/扫码数；`packaging.png` 与 `qr.png` 服务端生成；`scan` 写 `scan_event` 并广播 `trace.scanned`；`chat` 只使用已批准内容与引用证据，医疗/认证/保证类问题先模板拒答，LLM 回复再过 FactGuard 与数字白名单，失败降级模板。固定演示批次 `ZT-DEMO-001` 在 seed 时写入 `seed/demo_batch.json`（真实 V4.1 内容）+ 确定性定价 + 4 条 approved run/artifact，reset 后 H5 仍有完整内容。3D 礼盒正/背面贴包装 PNG，广告牌显示小红书标题，二维码立牌可点击打开 H5，批次沿 CatmullRom 路径移动，traced 后卡车驶出。

### Phase 4 · 图像与视觉打磨

真实图像 Provider；包装变体；色板/阴影/相机缓动；空态/错误态/加载态；性能与内存。

**验收**：1280×720 60fps；截图无溢出；无 key 时 mock 仍好看。

### Phase 5 · 加固与交付

单元/集成/Playwright 冒烟；demo reset 幂等；第二产品档案测试；Docker/一键启动；文档/来源/决策；验收清单。

**验收**：DoD 全过；新 Agent 只读文档能跑起来。

---

## 10. 验收标准（Definition of Done）

1. 四 Agent 端到端：建批次 → 故事 → 包装 → 内容 → 定价/溯源 → 扫码；每步有人工审核门。
2. 真实 LLM 模式与 mock 模式都可跑；无 key 不阻塞。
3. 包装图/文案/3D 贴图一致；二维码可扫到 H5。
4. 定价公式透明，溢价有公式 tooltip，基准有来源/日期，页面标注"演示测算"。
5. 沙盘可选站点/批次、相机可控、批次会移动、站点状态会变；60fps。
6. 溯源 H5 移动端可用，IP 对话有边界（不编食品安全/功效）。
7. `POST /api/demo/reset` 幂等；固定演示批次 `ZT-DEMO-001` / 溯源码 `ZTDEMO26` 不变。
8. 后端关键测试 + 前端 typecheck/lint/build + Playwright 冒烟全绿。
9. 文档：decisions v2、架构、Agent、数据、来源、runbook、AGENTS、README、05-next-steps。
10. 单产品 UI；第二产品档案测试通过，证明可复制。
11. 一键开发启动；可选 Docker；无外部服务依赖（mock 模式）。
12. 全中文 UI，无占位文案；演示数据有标识。

---

## 11. 风险与降级

| 风险 | 降级 |
|---|---|
| 图像 API 慢/失败/贵 | Mock/Pillow 合成兜底；结果缓存；现场不阻塞 |
| LLM JSON 不合法 | Pydantic 校验 + 修复 prompt 重试 1 次 + mock 兜底 |
| 3D 范围失控 | 固定场景 kit，不接自定义建模；instancing + DPR 上限 |
| 数据不准/来源冲突 | 区间 + 来源 + 日期 + "演示数据"；FactGuard 阻断 |
| SSE 断线 | 指数退避重连 + 重拉快照 + 轮询兜底 |
| SQLite 并发 | 单用户 + WAL；不跑多 worker |
| 版权 | 程序化资产；WareTrack 只参考模式/少量工具代码并标注；不搬资产 |
| 范围膨胀 | DoD + "不做什么"清单；新需求先记 decisions |

---

## 12. 文档与决策

- `docs/decisions.md` 是决策唯一真源，v2 已记录 #32–#58（范围、案例、栈、3D、Agent、Provider、SSE、知识库/FactGuard、包装、定价、溯源、验收、Phase 2 审核 UI 边界、Phase 3 公开溯源与 3D 联动、FactGuard 提问边界、品牌/IP 冻结）；本文只引用，不复制结论。
- `docs/v2/`：plan.md / ui.md / sources.md；architecture/agents/data/runbook/references 按需补。
- 重写 `AGENTS.md`（新命令、目录、env、测试方式、红线）、`README.md`、`docs/05-next-steps.md`。
- v1 设计文档已移除；如需追溯见 git history（main 分支）。
- 开发分支 `main`；完成可验证单元自动 commit，任务收口自动 push 到 `origin/main`（2026-10-22 起）；force/历史重写/删除远端分支仍先确认。
- `.gitignore` 已覆盖 `/data/`、`backend/data/`；不提交生成物/.env。

---

## 13. 不做什么

- 不做班次/任务/评分/城镇建造等游戏机制。
- 不做多产品 UI（只做第二个档案的测试夹具）。
- 不做登录/角色/多租户。
- 不接真实淘宝/抖音/小红书 API，不做真实爬虫；基准价用公开报价 + 来源。
- 不接 Canva/Midjourney 账号；用通用图像 Provider + 本地合成。
- 不做真实印刷生产/出血/色彩管理；导出仅示意。
- 不做移动端沙盘；只做移动端溯源 H5。
- 不做写实 3D/自定义 GLB 管线；低多边形程序化。
- 不做冷链温度曲线/IoT；溯源时间线只到批次事件。
- v2 核心不做真实农户语音 ASR；保留 Provider 接口，文本口述优先。

---

## 14. Phase 0 实施记录（2026-10-21）

- Phase 0 在 `rewrite/v2` 开发，后并入 `main`；旧 v1 backend/frontend 移出工作树。
- SQLite 9 张表 + Alembic 初始迁移；幂等 seed（1 产品 / 3 知识库占位 / 3 基准价 / 2 批次）。
- Mock LLM/Image Provider；`/api/health`、`/api/products`、`/api/batches`、`/api/demo/reset`。
- 后端 4 测试 + ruff 零告警；前端 React 19 + R3F 9 + Tailwind 4 骨架；3D 场景与 `/trace` 骨架。
- `pnpm typecheck/lint/build` 全绿；1280×720 桌面与 390×844 溯源页/桌面端提示视觉验收。
- 未实现：四 Agent 流水线、SSE、公开溯源 API/对话、包装合成、定价计算、真实图像生成；Phase 1 起补。
- v1 设计文档、探针报告、根目录旧 Postgres 数据（80MB）与 `.DS_Store` 已从工作树移除；追溯走 git history（main 分支）。

---

## 15. Phase 1 实施记录（2026-10-21）

- 四 Agent mock 流水线：story → packaging → marketing → pricing；统一状态机 + `AgentRun`/`Artifact`/workspace。
- 人工审核/驳回/重跑；SSE 事件总线；前端工位卡、JSON 审核 dialog、批次沿站点移动、审核后自动启动下一站。
- 验证：`pytest` 8 passed；`ruff` 零告警；`tsc`/`oxlint`/`vite build` 全绿；浏览器 batch 2 `traced`（四产出）与 batch 3 `packaging_review` 实测。
- Phase 1 结束时下一步：Phase 2 真实 Agent + 知识库/FactGuard + 包装合成 + 定价计算。


---

## 16. Phase 2 实施记录（2026-10-21）

- 知识库：`data/knowledge/zhaotong/` 10 篇 Markdown（GI/产地/品质/环境/文化/价格/包装/溯源/演示边界），seed 时 upsert 到 `knowledge_doc`；每条非演示事实带 `source_url + source_date`。
- 真实 Agent：`agents/engine.py` 统一生成器，Pydantic 结构化输出、失败重试 1 次、真实调用失败或无 key 时降级 mock；`AgentRun` 记录 `model/tokens/guard_json`。
- FactGuard：引用 doc_id 存在 + quote 逐字命中；拦截未认证/功效/保证/官方背书/“个个冰糖心”；数字未在引用文档或产品档案出现时 warning；审核通过前再校验一次。
- 定价：`services/pricing.py` 计算果价、损耗、分选、冷链、礼盒、平台/营销费、三档价格、毛利与溢价；LLM 只写解释，数字不一致时用模板；审核时服务端重算价格。
- 包装：`services/packaging.py` 用内置 Noto Serif/Sans 生成 1600×1000 PNG；固定品牌色角色避免模型色板顺序破坏版式；预览接口返回服务端 PNG；二维码指向 `/trace/{trace_code}`；审核通过后落盘，定价后重渲染为最终码。
- 前端：工位卡显示故事/包装/内容/定价专用预览、引用 chips、FactGuard 预警、模型/tokens；审核弹窗复用引用/预警/包装预览；新增 `/api/knowledge` 与 `/api/artifacts/{id}/file`。
- 验证：29 后端测试、ruff、typecheck/lint/build 全绿；真实 DeepSeek-V3.1-Terminus 批次 `ZT-2026-001` 走到 `traced`（`ZT0002`，156% 演示溢价）；营销 Agent 首次 90s 超时降级，提高到 180s 后成功。切换 V4.1-Flash 后重新验证故事（5161 tokens）与包装（11223 tokens），均无 fallback；旧 `traced` 批次未重跑。
- Phase 2 结束时未做：公开溯源 API/IP 对话、3D 贴图/广告牌联动、真实图像 Provider、字段级审核表单、扫码统计落库；其中公开溯源/H5/3D/扫码已在 Phase 3 补齐。

---

## 17. Phase 3 实施记录（2026-10-22）

- 公开溯源 API：`GET /api/trace/{code}`（大小写不敏感、未知码 404）聚合批次/产品/故事/包装/内容/价格/引用/时间线/扫码数；`packaging.png`、`qr.png` 服务端生成；`GET|POST /api/trace/{code}/scan` 写 `scan_event` 并广播 `trace.scanned`。
- H5：`/trace/:code` 390px 首屏（品牌/IP/包装图）、四 Agent 审核章、故事与 8 条引用、包装文案、旅程/审核时间线、价格卡（档位/溢价/公式/成本）、小红书内容卡、IP 对话、扫码计数；320px 无横向溢出；404/网络错误/骨架态。
- 对话边界：医疗/认证/保证类问题先模板拒答；LLM 只拿到已批准内容与引用证据；回复再过 FactGuard 与数字白名单，失败降级模板；`chat_message` 落库。
- 固定演示快照：`seed/demo_batch.json` 存真实 V4.1 的 story/packaging/marketing；seed 时为 `ZT-DEMO-001` 生成确定性定价、4 条 approved `AgentRun`/`Artifact`，`ZTDEMO26` reset 后仍有完整内容（runs 4 / artifacts 4）。
- 冻结品牌/IP：`specs.brand_name=乌蒙丑果`、`specs.ip_name=山风守园人`；系统提示与 mock 同步。
- FactGuard 修订：客服 `q` 字段不作为宣称；COMP-06 只拦“已获/获得/授权产品/官方认证”等宣称；降级原因带具体规则。
- 3D：礼盒正/背面贴包装 PNG，侧面/顶面牛皮纸；内容工坊广告牌显示小红书标题；云仓二维码立牌可点击打开 H5；批次沿 CatmullRom 路径移动；traced 后卡车驶出；左栏扫码数从 API 初始化并随 SSE 更新。
- 验证：39 后端测试、ruff、typecheck/lint/build 全绿（bundle 约 1.27MB，Phase 4 拆包）；V4.1-Flash 批次 `ZT-2026-005` 真实四站到 `ZT0006`，故事/包装/营销/定价 tokens 4925/12667/9059/4126，均无 fallback；reset 后 `ZTDEMO26` 200；H5 390×844/320px 与沙盘 1280×720 截图检查；二维码按钮打开新标签。
- 仍未做：字段级审核表单、真实图像 Provider、Playwright、第二产品档案夹具、长时 60fps/内存压测、80–85mm 三家价格/包装厂报价/地理标志公告原文。

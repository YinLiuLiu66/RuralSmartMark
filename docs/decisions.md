# 决策记录（Decisions Log）

> v1 决策 #1–#31 已随 v1 代码移除；如需追溯见 git history（main 分支）。
> 本文只保留 v2 决策（#32 起）。

---

## ✅ v2 重设计（2026-10-21）

> 本节为 v2 权威决策；v1 决策 #1–#31 已随 v1 代码移除（git history 可追溯）。旧代码、旧 CSS token、旧 Postgres/Docker 约定不作为实现约束。

### #32 · v2 重写范围
**结论**：greenfield 重写；单案例深做 + 可复制架构；不做多产品 UI；旧代码只保留在 git history。
**理由**：竞赛需要一个讲得深的故事，同时评委可能追问可复制性；用 ProductProfile/知识库/包装模板/基准价/场景预设留扩展口，不在 v2 做产品入驻。
**拍板时间**：2026-10-21

### #33 · 首个案例
**结论**：昭通丑苹果（云南省昭通市昭阳区）+ 虚构合作社子品牌（区域事实可查，品牌/人物演示合成）；替代 v1 的麻江蓝莓方案。
**理由**：丑苹果故事钩子强、视觉辨识度高、散装 vs 礼盒溢价容易讲清、公开资料足够；麻江蓝莓保留为第二个 ProductProfile 测试夹具。
**拍板时间**：2026-10-21

### #34 · 产品形态
**结论**：一个批次从原料到消费者的四站点品牌流水线（故事馆/包装工坊/内容工坊/云仓门店）+ 品牌护照 stepper + 人工审核门；不做游戏化任务/评分/班次。
**理由**：把四个 Agent 的产出挂在同一个批次对象上，避免四个孤立 Demo；审核门对应“AI 80% + 人 20%”叙事。
**拍板时间**：2026-10-21

### #35 · 技术栈
**结论**：前端 React 19 + TypeScript + Vite 8 + R3F 9 + Drei 10 + Zustand 5 + Tailwind CSS 4；后端 FastAPI + Pydantic v2 + SQLAlchemy 2.0 async + SQLite + Alembic；单用户免登录。
**理由**：greenfield 不继承 v1 的 React 18/纯 CSS/Postgres/JWT；SQLite 让演示零 Docker 依赖；R3F 与 Agent 工作台同栈。
**拍板时间**：2026-10-21

### #36 · 3D 沙盘
**结论**：桌面端等距正交 3D；构建方式对齐 WareTrack：代码拼 Box/Cylinder/Cone/Sphere/Plane + MeshStandardMaterial + CanvasTexture；低多边形程序化；不引 GLB/写实资产；手机不做 3D 沙盘。
**理由**：WareTrack 实测无 GLTFLoader/外部模型/贴图，完全程序化；同款构建方式可控、无美术依赖、性能稳定。手机只承载 `/trace/:code` 溯源 H5。
**拍板时间**：2026-10-21

### #37 · 四 Agent 流水线
**结论**：Story / Packaging / Marketing / Pricing+Trace 四个 Agent，统一 `AgentRun` 状态机（queued/running/waiting_review/approved/failed）；默认每步人工审核，`AUTO_APPROVE=true` 仅开发用。
**理由**：四步是竞赛叙事的主脊柱；审核门让人工润色可被看见；mock 先跑通再接真实模型。
**拍板时间**：2026-10-21

### #38 · Provider 抽象
**结论**：LLM/Image 均走 Provider 接口；无 key 用 Mock（文本 echo / Pillow 占位），有 key 再接 OpenAI 兼容端点与 SiliconFlow 图像；真实图像在 Phase 4。
**理由**：开发和测试不依赖网络/额度；Phase 0 已按此落地。
**拍板时间**：2026-10-21

### #39 · 数据与实时
**结论**：SQLite + 单 worker + 内存事件总线 + SSE；不引 Redis/Celery；写库成功后再广播。
**理由**：单用户演示足够；SSE 比 WebSocket 简单；与 v1 的“不做 SSE”相反，v2 以本节为准。
**拍板时间**：2026-10-21

### #40 · 知识库与事实边界
**结论**：昭通知识库 10–15 篇 Markdown，frontmatter 带 source_url/source_date/credibility；FactGuard 校验年份/比例/认证/人名/引用；口述标注“演示合成”；价格标“演示测算”。
**理由**：竞赛最怕编造；故事/定价必须可追溯；当前 sources.md 为 TODO 清单，Phase 2 前补齐。
**拍板时间**：2026-10-21

### #41 · 溯源 H5
**结论**：公开 `/trace/:code`；固定演示批次 `ZT-DEMO-001` / 码 `ZTDEMO26`；图文时间线 + 价格 + IP 人格对话；不做温度曲线/IoT。
**理由**：扫码闭环是四 Agent 的收口；固定码可提前印二维码；对话用已批准故事/事实做边界。
**拍板时间**：2026-10-21

### #42 · 定价口径
**结论**：Agent 4 的数字由确定性定价计算器产出（成本/毛利/溢价公式），LLM 只写解释；基准价必须带 source_url + date；页面标注“演示测算”。
**理由**：避免 LLM 算错/编价；评委可追问公式。
**拍板时间**：2026-10-21

### #43 · v2 不做什么
**结论**：不做游戏化、多产品 UI、登录/权限、真实电商 API、Canva/Midjourney 直连、IoT 温度曲线、移动端 3D、写实 GLB 管线。
**理由**：单案例深做；这些会稀释叙事或引入不可控外部依赖。
**拍板时间**：2026-10-21

### #44 · 文档边界
**结论**：v2 以 `docs/v2/plan.md` / `ui.md` / `sources.md` + 本节为准；v1 设计文档已移除；AGENTS/README/05 同步 v2。
**理由**：避免新 Agent 被 v1 的 Postgres/JWT/麻江/游戏化方案误导。
**拍板时间**：2026-10-21

### #45 · Phase 0 验收
**结论**：Phase 0 以“后端 4 测试 + ruff 零告警 + `pnpm typecheck/lint/build` + 1280/390 视觉验收”通过；不把未实现的流水线/SSE/溯源 API 说成已完成。
**验证**：见 docs/05-next-steps.md §0/§7。
**拍板时间**：2026-10-21

### #46 · Phase 1 流水线实现
**结论**：四 Agent 顺序状态机；`AgentRun` 先落库再广播；`/api/batches/{id}/workspace` 聚合 batch/runs/artifacts；SSE 用单 `message` 事件 + `type` 字段；审核通过后前端自动启动下一站；Phase 1 审核 UI 用 JSON 编辑器，Phase 2 换各 Agent 专用表单。
**理由**：先跑通端到端，再接真实模型；workspace 减少前端多次请求；单通道 SSE 简化重连；审核后自动启动让“通过并进入下一站”名副其实。
**验证**：pytest 8 passed；ruff/typecheck/lint/build 全绿；浏览器 batch 2 `traced` 四产出、batch 3 `packaging_review`。
**拍板时间**：2026-10-21

### #47 · 真实 Agent 运行时
**结论**：四个 Agent 共用一套 `AgentRuntime`（LLM Provider + 知识库 + 定价计算器 + 包装合成器）；输出用 Pydantic 模型校验，失败带错误信息重试 1 次；真实模型调用失败且 `LLM_FALLBACK_TO_MOCK=true` 时降级到确定性 mock，并在产出标 `demo=true` 与 `fallback_reason`；否则 run 失败、批次退回“可运行”状态，不进入审核。
**理由**：演示现场不能因为网络/额度直接断线；同时必须让人能分辨真实生成与降级 mock；失败不伪装成待审核。
**拍板时间**：2026-10-21

### #48 · 知识库与 FactGuard
**结论**：`data/knowledge/<product>/*.md` 是唯一事实源，seed 时 upsert 到 `knowledge_doc`；Agent 只能引用知识库里的 `doc_id`，引用 `quote` 必须逐字出现在正文；FactGuard 硬拦截未认证（有机/绿色食品/富硒）、医疗功效、保证增收/卖完、个个冰糖心；数字未在引用文档/产品档案中出现时给 warning 而非硬阻断；`credibility=demo` 的引用标“演示”，不当作事实背书。
**理由**：竞赛答辩最怕编造；逐字引用可机器校验，warning/error 分层避免因包装尺寸等正常数字误杀。
**拍板时间**：2026-10-21

### #49 · 包装合成与文件
**结论**：包装 Agent 输出结构化文案；`services/packaging.py` 原用同一份产出生成 SVG 预览与 Pillow PNG 落盘；预览接口 `GET /api/batches/{id}/agents/packaging/preview`（后由 #53 改为服务端 PNG），审核通过的 PNG 走 `GET /api/artifacts/{id}/file`；Phase 2 不接真实图像 API，3D 贴图在 Phase 3 消费该 PNG。
**理由**：SVG 可审可改、PNG 供 3D/导出；不引入 cairosvg/浏览器渲染依赖，Pillow 已有。
**拍板时间**：2026-10-21

### #50 · 确定性定价
**结论**：Agent 4 先由 `services/pricing.py` 算成本、三档价格、毛利与溢价；LLM 只写 rationale/greeting/FAQ，且 rationale 里的数字必须在允许集合内，否则用确定性模板替换；输出带 `formula` 与 `is_demo=true`。
**理由**：延续 #42，保证答辩时每个数字都能手算复现；LLM 不碰价格。
**拍板时间**：2026-10-21

### #51 · Phase 2 审核 UI 边界
**结论**：Phase 2 保留 JSON 编辑器，增加引用 chips、FactGuard 预警、包装预览（后由 #53 改为 PNG）；字段级专用表单推迟到 Phase 3，等四个 Agent 的 JSON 契约稳定后再做。
**理由**：真实 Agent 刚接入时字段还会调整，先做专用表单会返工；引用/预警/预览已经覆盖“人做 20% 判断”的关键信息。
**验证**：故事审核弹窗实测引用可点、预警可见、编辑后通过；服务端二次 FactGuard 与定价重算。
**拍板时间**：2026-10-21

### #52 · 推理预算与默认模型
**结论**：默认模型切到 `deepseek-ai/DeepSeek-V4.1-Flash`；通过 SiliconFlow 的 `extra_body.thinking_budget` 限制思维链，默认 2048（可配 128–32768，0 关闭），最终输出 `max_tokens=4096`；`reasoning_content` 仍不进入业务产出，只使用最终 `content`。
**理由**：V4.1-Flash 是推理模型，长思维链会拉高延迟和 token；2048 足够四类结构化产出，同时把最终 JSON 的预算单独留出。仍不把思维链拼回 Prompt，避免泄漏和解析污染。
**验证**：真实 API 短请求 1.3s/71 tokens；完整故事 Agent 5161 tokens、376 字无 fallback；包装 Agent 11223 tokens、无 fallback、FactGuard 零错误；界面显示新模型名。
**拍板时间**：2026-10-22

### #53 · 内置中文字体与包装预览
**结论**：内置 Noto Serif SC / Noto Sans SC 官方 `SubsetOTF/SC` 字体（Regular + Bold，约 40MB，OFL-1.1）；PNG 用内置字体渲染，Serif 做品牌/标题，Sans 做正文；包装预览接口改为服务端 PNG；SVG 渲染函数保留作后续导出，当前不提供导出入口。
**理由**：macOS 系统字体不可再分发，Linux/Docker 缺字体时 Pillow 会回退到无中文字形的默认字体；内置完整 SC 字库让预览和最终 PNG 跨机器一致，避免“Mac 正常、演示机方框”。预览改 PNG 是因为 SVG 由浏览器渲染，读不到后端内置字体。
**验证**：四份字体校验为 OpenType、合计约 40MB；`pytest` 29 passed；PNG 预览 `content-type=image/png`、1600×1000；真实包装稿用 Noto 渲染无缺字。
**拍板时间**：2026-10-22

### #54 · Phase 3 公开溯源与固定演示快照
**结论**：新增只读公开接口 `GET /api/trace/{code}`（批次、四章产出、引用、价格、时间线、扫码数）、`GET /api/trace/{code}/packaging.png`、`GET /api/trace/{code}/qr.png`、`GET/POST /api/trace/{code}/scan`、`POST /api/trace/{code}/chat`；未知码 404，大小写不敏感。H5 `/trace/:code` 移动优先 390px，含首屏、故事、包装文案、旅程/审核时间线、价格与公式/成本、内容卡、IP 对话、扫码计数。对话只使用已批准故事/包装/定价与引用证据；医疗/认证/保证类问题先模板拒答，LLM 回复再过 FactGuard 与数字白名单，失败降级模板。固定演示批次 `ZT-DEMO-001` / `ZTDEMO26` 在 seed 时写入真实 V4.1 内容快照（`seed/demo_batch.json`）+ 确定性定价 + 4 条 approved `AgentRun`/`Artifact`，`POST /api/demo/reset` 后仍有完整内容。
**理由**：扫码闭环不能只印一个空壳二维码；固定码必须在离线/reset 后可复现；公开页只暴露价格档位、溢价、公式与成本构成，不暴露毛利字段；对话必须能拒绝功效/认证类问题，不能把 LLM 的自由回答直接放出去。
**验证**：39 后端测试；`ZT-2026-005` 用 V4.1-Flash 四站真实生成到 `ZT0006`（无 fallback，故事/包装/营销/定价 tokens 分别 4925/12667/9059/4126）；reset 后 `ZTDEMO26` 返回 200、4 条 approved 产出、扫码/对话可用；H5 在 390×844 与 320px 视口截图检查，无横向溢出；真实对话回答价格问题，医疗问题模板拒答。
**拍板时间**：2026-10-22

### #55 · 3D 沙盘联动
**结论**：3D 礼盒使用已通过的包装 PNG 作为正/背面纹理，侧面/顶面保持牛皮纸色；内容工坊前广告牌显示营销标题；云仓旁二维码立牌显示 `qr.png`，点击打开 `/trace/{code}`；批次沿 CatmullRom 路径在六站点间移动；`traced` 后卡车驶出；左栏扫码数从 `GET /trace/{code}/scan` 初始化，并通过 SSE `trace.scanned` 更新。广告牌/二维码用 Html 覆盖层保证中文和二维码清晰，礼盒仍用 Three 纹理。
**理由**：竞赛现场首先看“批次真的走完、盒子真的有包装、二维码真的能扫”；纯 CanvasTexture 广告牌在正交相机和远景下文字过小，Html 覆盖层更可靠；二维码需要可点击，不能只是贴图。
**验证**：1280×720 浏览器实测固定演示批次：礼盒红/奶油标签、广告牌标题、二维码、卡车出库均可见；二维码按钮打开 `/trace/ZTDEMO26` 新标签；扫码计数显示 1 次并与接口一致。
**拍板时间**：2026-10-22

### #56 · FactGuard 提问/宣称边界
**结论**：客服问答的 `q` 字段是提问，不按对外宣称校验；COMP-06 只拦“已获/获得地理标志授权、地理标志授权产品、授权使用、政府指定、官方认证/推荐/授权”等宣称，不再拦“有没有地理标志授权”这类提问或澄清；真实产出降级时 `fallback_reason` 带前两条校验规则，审核界面能看到降级原因。
**理由**：旧规则把“你们有地理标志授权吗？”当成违规，导致营销 Agent 两次重试后仍降级；把提问和宣称分开，既保留合规拦截，又让客服能明确回答“没有”。
**验证**：新增 FactGuard 测试覆盖提问通过、宣称拦截；引擎测试覆盖降级原因带 `COMP-02`；营销 Agent 重跑后真实通过（9059 tokens）。
**拍板时间**：2026-10-22

### #57 · 品牌与 IP 冻结
**结论**：品牌名固定为「乌蒙丑果」，IP 名固定为「山风守园人」；写入 `ProductProfile.specs.brand_name/ip_name` 与 Agent 系统提示，mock 同步；IP 是演示合成的守园人角色，不是真实果农，不得另起名。
**理由**：故事、包装、内容、H5 需要一个稳定的品牌记忆点；每次生成不同 IP 会让包装和物料对不上，也会削弱答辩叙事。
**验证**：产品档案 seed 后含两个字段；V4.1 故事 Agent 输出 `ip_name=山风守园人`；包装正面为「乌蒙丑果｜山风守园人」；H5 首屏与对话均使用该名。
**拍板时间**：2026-10-22

### #58 · 字段级审核表单推迟
**结论**：字段级审核表单不在 Phase 3 做；当前 JSON 编辑器 + 引用/预警/包装预览已覆盖审核门。Phase 4 优先真实图像与视觉打磨，Phase 5 视时间补字段级表单，不阻塞主流程。
**理由**：Phase 3 的重点是扫码闭环与 3D 联动；四个 Agent 的 JSON 契约刚稳定，此时做字段级表单容易返工；JSON 编辑器能完整表达所有字段，现场审核可用。
**验证**：Phase 3 真实批次与固定演示批次均通过 JSON 审核/seed 快照进入 `traced`；字段级表单缺口已记入 `05-next-steps.md`。
**拍板时间**：2026-10-22

### #59 · 真实图像 Provider 与 IP 插画
**结论**：接入 SiliconFlow `POST /v1/images/generations`，默认模型 `Tongyi-MAI/Z-Image-Turbo`（可切 `Tongyi-MAI/Z-Image`）；竖版生图用 768×1024，按调用尺寸自动落到 512×512 / 1024×576 / 768×1024，可用 `IMAGE_SIZE` 覆盖；带负向提示词，保留服务端默认“AI 生成”水印。生成结果下载后转 PNG，按 `model+prompt+size+negative_prompt` 的 SHA-256 缓存到 `backend/data/image-cache/`。包装审核通过后先生成 `illustration` artifact，失败只记录 `demo=true/error`，不阻塞审核。固定演示批次提交一张同 prompt 的 Z-Image-Turbo 快照 `seed/demo_illustration.png`，H5 故事区和包装工位展示。
**理由**：Z-Image-Turbo 约 ¥0.1/张、实测约 3 秒，中文与画面文字渲染好；审核通过后再生图，避免未通过稿浪费额度；缓存避免重跑重复扣费；固定演示码需要离线可复现，所以提交一张快照而不是现场依赖网络。
**验证**：真实 API 512×512 与 768×1024 均 200；Provider 类实测 768×1024、约 986KB、缓存命中；`seed/demo_illustration.png` 为 768×1024、保留“AI 生成”水印；H5 与包装工位均显示；43 后端测试、ruff、前端 typecheck/lint/build 全绿。
**拍板时间**：2026-10-22

### #60 · Phase 4 包装变体、加载态与代码分割
**结论**：包装提供 3 个视觉变体「经典牛皮纸 / 山野红 / 夜绿」，后端 `GET /api/batches/{id}/agents/packaging/variants` 为权威列表，预览与溯源图支持 `?variant=`；变体只改色板，不改文案、结构或事实。前端包装工位显示变体 chips，选择写入 Zustand，3D 礼盒贴图同步。路由与 `Scene` 改为 `lazy` + Suspense，增加 `SceneBoundary`（WebGL 失败可重试）、加载骨架、API 错误重试和空批次新建按钮；OrbitControls 开阻尼。Phase 4 以此为收口，长时 60fps、200% zoom 与 Playwright 留给 Phase 5。
**理由**：包装变体是最能体现“同一份 Agent 产出可探索不同视觉方向”的交互；变体只动色板，避免把未审核的结构/事实写进画面。代码分割把 H5 与 three.js 隔开，手机打开溯源页不再下载 950KB 的 3D chunk；加载/错误态让现场网络波动时不至于白屏。
**验证**：`43` 后端测试；`variants` 返回 3 项，`preview?variant=crimson` 与默认图不同，未知变体 422；溯源 `packaging.png?variant=night` 200；1280×720 场景 2.5 秒采样 120fps（高刷屏）；`pnpm build` 产出 index 260KB、Sandbox 37KB、Trace 23KB、Scene 950KB 异步 chunk；H5 与包装工位截图确认变体切换和插画。
**拍板时间**：2026-10-22

### #61 · Phase 5 自动化验收与一键启动
**结论**：前端引入本地 `@playwright/test`（不入全局），配 `frontend/playwright.config.ts` 与 `e2e/` 两组冒烟：桌面沙盘加载固定演示批次、包装变体与插画、3D 二维码打开 H5；移动 H5 完整展示、扫码计数、320px 无溢出、未知码/超长码 404。性能用例单独 `perf` project：固定演示批次 60 秒采样帧率与 JS 堆，200% 等效视口（640×360）验证桌面提示回退且无横向溢出。新增根 `Makefile` 的 `dev/test/e2e/perf`，Playwright 的 `webServer` 在未启动时自动拉起后端（迁移 + seed）与前端。`/api/demo/reset` 回归增加“扫码后 reset 归零、重复 reset 不产生重复 run/artifact”。沙盘首次加载优先选中 `ZT-DEMO-001`，其次任一 `traced` 批次，避免现场落在 raw 批次。
**理由**：此前只有手动浏览器验收，Phase 5 需要可重复证据；Playwright 本地 devDependency + Chromium 缓存不污染系统；性能用例与冒烟分开，避免每次都跑 60 秒。
**验证**：`pnpm test:e2e` 6 passed；`PERF_SECONDS=60 pnpm test:perf` 2 passed（58.3fps、44.5MB→42.4MB、640×360 无溢出）；后端 44 tests、ruff、前端 typecheck/lint/build 全绿。
**拍板时间**：2026-10-22

### #62 · 第二产品档案夹具与档案化输出
**结论**：用麻江蓝莓做**只建数据**的第二档案夹具（`backend/tests/fixtures/majiang/`）：产品 JSON + 6 篇明确标注 `credibility=demo` 的知识库 + 3 条基准价；pytest 用 mock LLM 跑完整四站，断言 `traced`、`MJ` 前缀溯源码、H5 公开数据与包装 PNG，并断言输出不含昭通/乌蒙/山风/苹果。为让“换档案不改代码”成立，系统提示、Agent brief、mock 文案、定价档位/标签/欢迎语/时间线/FAQ、包装品牌字与页脚、溯源码前缀均改为从 `ProductProfile.specs` 读取，昭通默认值保持不变。第二档案不进入 seed、不建 UI、不做第二套 3D。
**理由**：DoD 要求证明可复制；只加数据不改核心代码，才是可复制的证据。夹具数据全部标 demo，避免把测试数据当成真实麻江蓝莓事实。
**验证**：`test_second_product_runs_without_code_changes` 通过；全量 44 tests；昭通固定演示码 `ZTDEMO26` 与 156% 溢价回归不变。
**拍板时间**：2026-10-22

### #63 · Phase 5 收口：字段级表单与 Docker 不做
**结论**：字段级审核表单继续保留 JSON 编辑器方案（沿用 #58），Docker 不做；开发启动用根 `Makefile` 的 `make dev`（uv + pnpm 本地进程），不引入容器依赖。真实盒型/刀版、生图失败视觉兜底、缓存清理、手机真机扫码、真实价格/包装厂报价/GI 公告原文仍列为后续核验项，不阻塞当前演示。
**理由**：当前审核 UI 已覆盖引用、预警、包装预览与 JSON 编辑，竞赛现场可用；Docker 与项目“无外部服务依赖、SQLite 本地跑”的取舍冲突，收益低。把时间留给可重复验收与第二档案证据。
**验证**：`make -n dev` 正确展开；`make test`/`make e2e`/`make perf` 可执行；缺口已同步 `docs/05-next-steps.md`。
**拍板时间**：2026-10-22

### #64 · LLM 输出忽略未知字段
**结论**：`agents/schemas.py` 的输出模型从 `extra="forbid"` 改为 `extra="ignore"`；LLM 多写的未知键直接丢弃，必填字段、类型、长度、成本等式等已知约束仍严格校验。
**理由**：真实 V4.1-Flash 在第二产品营销输出里多写了一个 `wechat.title_note: null`，导致 Schema 校验失败并整站降级 mock；一次空字段抖动不该让审核卡住。忽略未知字段比放宽已知字段校验更可控。
**验证**：`RSM_REAL_LLM=1 uv run pytest tests/test_second_product_real.py` 通过：四站 `model != mock`、无 fallback、`MJ` 溯源码、输出无昭通/苹果残留；常规 `uv run pytest` 52 passed + 2 skipped（真实 LLM 测试默认跳过）。
**拍板时间**：2026-10-22

### #65 · 生图缓存清理与失败兜底
**结论**：新增 `services/image_cache.py` 与 `python -m ruralsmartmark.maintenance image-cache`，默认删除 30 天前的 PNG，并把目录压到 512MB 以内（先删最旧文件）；支持 `--dry-run`，不做启动时自动删除。包装工位的插画加载失败或 artifact 带 `error` 时显示「插画这次没有生成 / 包装审核不受影响」的视觉兜底卡，不再只留一行提示；H5 在无插画 URL 或图片加载失败时省略插画区，不显示破图。
**理由**：生图缓存只增不减会占满本地盘；自动清理可能在演示前误删固定素材，所以做成显式命令。失败兜底要让审核者一眼看出“包装产出仍然有效”，而不是怀疑整站坏了。
**验证**：`tests/test_image_cache.py` 覆盖过期、超容量、dry-run 三种情况；Playwright 新增“插画生成失败时显示视觉兜底”用例，当前 9 条冒烟全过；`maintenance image-cache --dry-run` 可打印扫描/将删除/保留统计。
**拍板时间**：2026-10-22

### #66 · 局域网扫码演示模式
**结论**：新增 `make lan` / `scripts/lan-demo.sh`：自动检测 `en0`/`en1` 的局域网 IP，前端用 `vite --host 0.0.0.0 --strictPort`，后端用 `PUBLIC_BASE_URL=http://<LAN_IP>:5173` 启动，启动后自动 `POST /api/demo/reset`，让固定演示码二维码指向局域网地址。默认 `make dev` 仍只绑 `127.0.0.1`；`make lan` 只用于可信局域网，Ctrl-C 同时停止前后端。
**理由**：真机扫码是剩余验收项，而二维码内容由 `public_base_url` 生成；如果只开 Vite 的 LAN 监听但不重置演示数据，旧二维码仍指向 127.0.0.1。把 IP 探测、监听、重置和退出收在一个脚本里，现场只需 `make lan` 然后拿手机扫。
**验证**：本机检测到 `172.20.10.13`；`http://172.20.10.13:5173/`、`/trace/ZTDEMO26`、`/api/trace/ZTDEMO26/qr.png` 均 200；workspace 中 `pricing.qr_payload` 为 `http://172.20.10.13:5173/trace/ZTDEMO26`。真机扫描仍需用户在同一 Wi-Fi 下完成。
**拍板时间**：2026-10-22

### #67 · 项目正式名与命名层级
**结论**：项目正式名为《“智农云链”——基于多智能体协同的县域农产品品牌数字化重构系统》。界面、文档、包装系统署名与 Agent 系统提示统一使用“智农云链”；演示案例仍为昭通丑苹果，虚构合作社品牌仍为“乌蒙丑果”，IP 仍为“山风守园人”；`RuralSmartMark` 只保留为仓库/代码标识。原“乡土印记”作为系统名的用法退役。
**理由**：答辩、README、界面标题和包装署名必须与正式项目名一致；“智农云链”是系统名，不能和合作社品牌、IP、产品案例混成一个名字。保留代码标识避免无意义地改包名、数据库路径和历史提交。
**验证**：前端标题/首屏/溯源页/包装 PNG 系统署名均为“智农云链”；README、AGENTS、plan、ui、backend/frontend README 同步；昭通案例的“乌蒙丑果”“山风守园人”与固定演示码不变。
**拍板时间**：2026-10-22

### #68 · 多产品工作台
**结论**：从单产品工作台改为多产品列表/切换器；每个产品拥有独立知识库、基准价、批次、产出与溯源码。顶栏增加产品选择与「新建产品」；批次按产品过滤。原先“不做多产品 UI”的红线由此条替代。
**理由**：用户要“让系统为我所用”，必须能建档自己的产品；单产品 UI 只能演示昭通案例。多产品只切换数据，不并列渲染多个 3D 场景，仍保持单工作台。
**验证**：两个产品同用 `ORIGIN-01` 不冲突；切换产品后批次/知识库/文案随产品变化。
**拍板时间**：2026-10-22

### #69 · 单入口总控
**结论**：新增“总控”控制面，用户只在一个对话输入框里调研、追问、修改、通过、回退。总控不是第五个生成 Agent，而是读取所有产品/批次/AgentRun/Artifact，调用现有四站 Agent。动作白名单化；建档、通过、驳回、回退必须二次确认；运行 Agent 和读操作可直接执行。步数用 PydanticAI `UsageLimits`，实测 4 轮模型请求/8 次工具调用不够，默认调整为 10 轮/12 次，可配置。
**理由**：四个独立工位适合审核，但不适合用户表达“我想做某产品”和“包装改一下”；单入口降低操作成本。不让模型直接执行 SQL/文件/任意 HTTP，避免不可控副作用。
**验证**：mock 流程“问 → 查 → 草案 → 确认建档”；修改当前站/回退早期站均通过；确认卡拦截危险动作。
**拍板时间**：2026-10-22

### #70 · Firecrawl 搜索与抓取
**结论**：搜索/抓页用 Firecrawl SDK（后端项目 venv 安装），Provider 抽象保留 Tavily 备选。搜索一次最多 5 条，抓取一次最多 4 页；key 只进 `backend/.env`。无 key 时总控提示贴链接/原文，不静默失败。
**理由**：整页 Markdown + PDF 适合逐字引用；免费 1000 credits/月、搜索 2 credits/10 条、抓取 1 credit/页，够演示。Tavily 更轻但内容可能偏摘要，逐字引用不如原文稳。
**验证**：`RSM_REAL_SEARCH=1` 搜索/抓页测试通过；真实麻江蓝莓调研草案拿到 1 条搜狐来源、逐字校验通过，价格/包装/品牌缺失转为追问；无 key 路径返回可操作提示。
**拍板时间**：2026-10-22

### #71 · 早期站点回退语义
**结论**：允许修改早期站点。确认后清空下游 `batch.*_json`、删除下游 Artifact/插画文件、下游 run 标记 failed（error=`rewound by controller`），批次回到目标站可运行状态并重跑；历史 AgentRun 保留作审计。
**理由**：用户说“包装不好改一下”时，下游内容和定价必须失效，否则溯源页会混用旧产出。直接删历史会丢审计，所以只作废产出、保留 run。
**验证**：回退后下游 artifact 不残留、批次状态正确、重跑后新产出替换旧内容。
**拍板时间**：2026-10-22

### #72 · 总控流式回复与思维链
**结论**：总控改为 SSE 流式（`POST /api/controller/sessions/{id}/messages/stream`），回答按 token 推送；模型 `reasoning_content` 作为「思考过程」逐行展示，默认折叠。控制器输出从结构化 `ControllerReply` 改为纯文本 `str`，草案与待确认动作仍由工具和动作白名单捕获。用户消息先落库并立即在前端乐观显示，不再等整轮结束才出现。Firecrawl 改用 `AsyncFirecrawl`，默认绕过系统代理（`FIRECRAWL_TRUST_ENV=false`），网络类失败自动重试并转成中文可操作提示。
**理由**：总控一轮可能包含搜索、抓页、多个工具调用，非流式下用户几十秒看不到任何反馈；先显示自己发的话是聊天界面的基本预期。DeepSeek 的思维链能帮助用户判断总控为什么查/为什么停，但不应作为事实来源，所以只展示、不写入知识库。
**验证**：真实模型流式测试收到 thinking/delta 事件并保存思考行；`curl -N` 验证 SSE 顺序为 user → thinking/delta → done；Playwright 新增“先显示用户消息、思维链默认折叠”用例；真实 Firecrawl 搜索/抓页在绕过系统代理后通过。后端 55 passed + 2 skipped，Playwright 10 条。
**拍板时间**：2026-10-22

### #73 · 新建产品使用空白总控会话
**结论**：`POST /api/controller/sessions` 增加 `fresh` 参数；顶栏「+」、总控面板「新建」与 `/controller` 页的「新建」都创建 `product_id=null, batch_id=null` 的空白会话，不再复用当前产品/批次的会话。确认建档后，会话自动绑定新产品与首批次；默认 `fresh=false` 仍按 `(product_id, batch_id)` 复用最近会话。
**理由**：原入口只是打开当前产品会话，模型上下文带着昭通苹果，用户做新产品时容易被旧批次干扰；空白会话把“新产品调研”和“当前批次修改”彻底分开。
**验证**：`test_fresh_session_skips_existing_blank_session` 覆盖强制新建与默认复用；Playwright 新增“新建产品打开空白总控会话”，断言请求体 `fresh=true` 且产品/批次为 null。后端 56 passed + 2 skipped，Playwright 11 条。
**后续**：#75 将 `fresh=true` 调整为“复用唯一空白会话，没有才新建”，避免同时出现多个空沙盘。
**拍板时间**：2026-10-23

### #74 · 总控确认通过后自动继续下一站
**结论**：总控的 `approve_agent` 确认卡执行通过后，后端自动启动下一站 Agent（故事→包装→营销→定价）；定价通过后直接进入 `traced`，不再启动下一站。下一站仍在生成完成后停在待审核，必须再由用户确认，不做连续自动通过。若下一站启动失败，审核结果保留，回复说明失败原因并提示到对应工位重跑。
**理由**：沙盘 UI 的“通过并进入下一站”已经是这个语义，总控若只通过不继续，用户还得再说一次“运行下一站”，两条入口行为不一致。保留逐站确认，避免总控替用户连续放行四站。
**验证**：`test_confirm_approve_continues_next_station` 断言通过故事后自动调用包装 Agent 并停在 `packaging_review`；常规 `uv run pytest` 57 passed + 2 skipped。
**拍板时间**：2026-10-23

### #75 · 新建先进入空沙盘，且空白沙盘单例
**结论**：点顶栏「+」或总控「新建」先进入客户端空沙盘：不创建产品/批次，产品与批次下拉显示“新产品（未建档）/未创建批次”并禁用；同一时间只保留一个空白沙盘。`fresh=true` 时若已有未建档空白会话则复用最新一条，没有才新建；确认建档后会话绑定新产品/首批次，沙盘退出空态并切到新批次。
**理由**：用户点「新建」需要看到“真的腾出了一个新地方”；连续点击不能制造多个空会话/空沙盘，也不能留下无主数据。
**验证**：`test_fresh_session_reuses_single_blank_session` 覆盖首次复用、再次复用、建档后新建；Playwright 断言点「新建」出现空沙盘、下拉为占位、重复点击仍保持同一空态。后端 57 passed + 2 skipped，Playwright 11 条。
**拍板时间**：2026-10-23

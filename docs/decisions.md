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

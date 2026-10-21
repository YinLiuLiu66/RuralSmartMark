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

# 智农云链 v2 · 前端设计契约

> 正式名：《“智农云链”——基于多智能体协同的县域农产品品牌数字化重构系统》  
> 状态：已实施（Phase 0–5，2026-10-22；frontend-craft 流程第 1–6 步）  
> 日期：2026-10-21  
> 视觉方向：山野编辑部（暖色纸感、衬线标题、低多边形乡村、非 WMS 冷色控制塔）  
> 重写原则：greenfield。旧前端代码、旧 CSS token、旧版本约定不继承；本文是 v2 的唯一前端设计源。  
> 说明：本文不写代码；实现完成后按第 7 节在 1280/1440 与 390 宽度做视觉验收并补截图。

## 1. 六行设计契约

```
Platform / surface:  desktop web 1280–1920；3D 沙盘 + 覆盖式工作台；移动端只做 /trace H5（390px 起）
User job:            把一个苹果批次依次过四个 Agent，审核产出，看到溢价与溯源码
Primary action:      「运行流水线」/「通过并进入下一站」——同一时刻只允许一个主按钮
Lead value:          品牌护照进度（如「3/6 · 包装待审核」）；溢价率是支持指标，不是主视觉
States:              无批次 / idle / running / waiting_review / approved / failed / SSE 重连 / loading / 极端内容
Borrowed patterns:   顶栏 + 批次切换、右侧上下文卡、底部 stepper、Tabs、原生 <dialog> 审核、Toast、Skeleton
```

**Out of scope**：游戏化任务/评分、多产品 UI、登录/权限、移动端沙盘、真实电商 API、Canva/Midjourney 直连。

### 契约已经决定的几件事

- 主按钮同一时刻只有一个：顶栏「运行流水线」和右卡「通过并进入下一站」互斥，不并列。
- 品牌护照进度是首屏主角；溢价率、故事、内容、扫码只做支持指标，不做五张等权 KPI 卡。
- 审核是短任务，用原生 `<dialog>`；不跳页、不嵌套弹窗。
- 站点/批次/门店是 peer 对象，用右侧上下文卡切换；不做多层导航。
- 移动端只承载溯源 H5；沙盘在 <1024px 显示“请用桌面端”，不硬做响应式 3D。

## 2. 设计 token

> Tailwind v4 `@theme` 映射这些角色；组件只引用角色名，不写 raw hex。  
> 对比度已按 WCAG 计算：正文 13.40:1、次要文字 5.40:1、苹果红 5.50:1、叶绿 6.03:1、琥珀 5.83:1、危险 6.43:1、强边框 3.62:1。  
> `--kraft` 仅作装饰（2.29:1，不可用于文字）；`--ink-faint` 仅作非必要信息。

```css
:root {
  color-scheme: light;

  /* surfaces */
  --paper: #f7f3ea;
  --surface: #fffdf8;
  --surface-2: #f0eadf;

  /* ink */
  --ink: #1f2a24;
  --ink-muted: #5f655f;
  --ink-faint: #8a8a80;

  /* lines */
  --line: #e0d8c8;
  --line-strong: #8a8578;

  /* brand */
  --apple: #b6402a;
  --apple-hover: #96311f;
  --apple-weak: #f7e4de;
  --leaf: #3f6b4f;
  --leaf-weak: #e6efe8;
  --amber: #8a5a00;
  --danger: #b3261e;
  --kraft: #c9a46a; /* decorative only */

  /* focus / motion */
  --focus: #b6402a;
  --ring: 0 0 0 3px color-mix(in srgb, var(--focus) 28%, transparent);
  --ease: cubic-bezier(0.2, 0.7, 0.2, 1);
  --dur: 180ms;

  /* type */
  --font-display: "Songti SC", "STSong", "Noto Serif SC", "Source Han Serif SC", serif;
  --font-ui: "PingFang SC", "Noto Sans SC", "Microsoft YaHei", system-ui, sans-serif;
  --fs-12: 12px;
  --fs-13: 13px;
  --fs-15: 15px;
  --fs-20: 20px;
  --fs-28: 28px;
  --fs-40: 40px;
  --fs-56: 56px;
  --lh-tight: 1.15;
  --lh-body: 1.55;

  /* space: 4/8 */
  --s-1: 4px;
  --s-2: 8px;
  --s-3: 12px;
  --s-4: 16px;
  --s-6: 24px;
  --s-8: 32px;
  --s-12: 48px;

  /* radius: two + pill */
  --r-control: 10px;
  --r-card: 16px;
  --r-pill: 999px;

  /* elevation: one direction */
  --shadow-card: 0 1px 2px rgb(31 42 36 / 0.06), 0 10px 30px rgb(31 42 36 / 0.08);
  --shadow-float: 0 18px 50px rgb(31 42 36 / 0.16);
}
```

**规则**

- 不引入暗色模式；`color-scheme: light`。暗色不在 v2 范围，避免两套对比度维护。
- 衬线只用于标题、品牌名、故事正文；UI 控件、数字、按钮用无衬线。数字全部 `font-variant-numeric: tabular-nums`。
- 字体不依赖外部 CDN；PNG 用内置 Noto Serif/Sans（OFL）；SVG 保留系统字体栈；构建时不下载字体。
- 两个饱和色同时可见的上限：苹果红（主操作/选中）+ 叶绿（完成/成功）；牛皮纸只做背景纹理/装饰，不承担语义。
- 无渐变、无玻璃拟态、无 emoji 状态图标；图标统一用 lucide，线宽一致。

## 3. 布局与信息层级

### 桌面布局（≥1280）

```
┌──────────────────────────────────────────────────────────────┐
│ 顶栏 64：Logo / 批次切换 / 状态 pill / 运行流水线 / 通知 / 设置 │
├───────────────┬──────────────────────────────┬───────────────┤
│ 左栏 280       │ 中央 3D 沙盘                  │ 右栏 360       │
│ 品牌护照 lead  │ 果园/故事馆/包装/内容/云仓     │ 上下文卡       │
│ 4 个支持指标   │ 相机控件（左中）              │ 主操作 + 预览  │
│ 当前批次摘要   │ 浮动标签/选中框               │ 日志（折叠）   │
├───────────────┴──────────────────────────────┴───────────────┤
│ 底部 dock 108：品牌护照 stepper  |  产出物 Tabs                │
└──────────────────────────────────────────────────────────────┘
```

- **Lead value**：左栏第一块是「品牌护照」卡，40px 的 `3/6` 或当前阶段名「包装待审核」，下方 6 个进度点；不要做成五张同尺寸 KPI 卡。
- **支持指标**：溢价率（定价前显示“待测算”）、故事定稿、内容素材、扫码次数，2×2 网格；每个指标有标签、值、单位/状态。
- **中央**：3D 场景占最大面积；不要在画布上叠太多卡；相机控件靠左中，图例/操作提示靠左下，均半透明纸卡。
- **右栏**：上下文卡只服务一个选中对象；顶部对象名 + 状态 chip，中部关键字段，底部一个主操作；日志和原始 JSON 折叠在“详情”里。
- **底部 dock**：左侧 stepper（6 步）是叙事脊柱；右侧产出物 Tabs 是快捷入口。两者不要互相复制信息。
- **顶栏**：批次切换是下拉（一个产品下 1–N 个批次）；状态 pill 用文字 + 小圆点，不用彩色大横幅。
- **响应式**：1440 以上右栏 360；1280–1439 右栏 320；<1280 右栏变抽屉（默认关）；<1024 沙盘显示桌面端提示，不缩成手机版 3D。

### 层级顺序

1. 我在哪一批 / 走到哪一步（lead value）
2. 下一步该做什么（primary action）
3. 结果如何（溢价、素材、扫码）
4. 当前选中对象的细节（right rail）
5. 历史与调试（logs、raw JSON、settings）

### 内容规则

- 所有价格/溢价带“演示测算”标签和公式 tooltip；不把演示值写成市场事实。
- 所有 Agent 产出显示状态：待运行 / 运行中 / 待审核 / 已通过 / 失败；失败保留已有内容 + 重试。
- 长文本（故事、脚本）在右栏只显示 6–8 行摘要，完整内容进 `/batch/:id` 或展开面板。
- 空态必须给下一步动作：无批次 →「新建批次」；无产出 →「运行流水线」；无扫码 →「模拟扫码」。

## 4. 组件清单

### Shell / 布局

| 组件 | 责任 | 关键状态 |
|---|---|---|
| `AppShell` | 顶栏 + 左/中/右 + dock 的网格 | loading / ready / sse-offline |
| `TopBar` | 品牌、批次切换、状态 pill、主按钮、通知、设置 | idle / running / waiting_review / failed |
| `LeftRail` | Lead passport、支持指标、当前批次摘要 | empty / loading / extreme |
| `CanvasStage` | R3F Canvas + 相机 + 选中 + 浮动标签 | webgl-error / loading / ready |
| `RightRail` | 上下文卡容器；<1280 变抽屉 | open / closed |
| `BottomDock` | stepper + 产出物 Tabs | loading / empty |

### 基础 primitives

`Button`（primary/secondary/ghost/danger）、`IconButton`、`Card`、`StatusChip`、`ProgressDots`、`Tabs`、`Dialog`（原生 `<dialog>`）、`Field`、`Textarea`、`Select`（原生）、`Toast`、`Tooltip`、`Skeleton`、`EmptyState`、`ErrorBanner`。

规则：一个 Button、一个 Input、一个 Dialog、一个 Card；同义操作同名（“运行流水线”“通过并进入下一站”“重跑”），不在不同屏幕换词。

### 沙盘

`Scene`、`Ground`、`Orchard`、`StationBuilding`、`BatchPallet`、`Truck`、`CameraRig`、`SelectionOutline`、`FloatingLabel`、`StationPulse`、`Billboard`、`QrSign`。

- 站点建筑：故事馆（书/卷轴意象）、包装工坊（屋檐 + 木箱）、内容工坊（直播屏/广告牌）、云仓/门店（仓门 + 二维码立牌）。
- 批次：托盘 + 纸箱；包装前牛皮纸毛坯，包装后换生成贴图；沿 CatmullRom 移动。
- 选中：点击站点/批次/门店；outline + 浮动标签；点空白取消。
- 相机：拖拽平移、滚轮/双指缩放、旋转按钮 45°、复位缓动；极角限制在等距范围。

### 工作台

`LeadPassportCard`、`MetricGrid`、`StationCard`、`BatchCard`、`StoreCard`、`ReviewDialog`、`ArtifactTabs`、`ArtifactPreview`、`AgentLog`、`RerunNote`、`PhonePreview`、`CameraControls`。

- `StationCard`：Agent 名/角色、状态、当前任务、输入摘要、产出预览、主操作（运行/通过）、次操作（重跑/查看日志）。
- `ReviewDialog`：标题写明站点和批次；可编辑字段；底部主按钮“通过并进入下一站”，次按钮“驳回/稍后”；Esc/遮罩关闭；破坏性操作不默认聚焦。
- `ArtifactTabs`：故事 / 包装 / 内容 / 定价 / 溯源；每个 tab 显示状态点；不把 5 个 tab 做成 5 张卡。
- `PhonePreview`：未单独做 390px 手机框；3D 二维码按钮直接打开 H5 新标签（decisions #55）。

### 溯源 H5（Phase 3 已实现）

`TraceHero`、`StorySection`、`Timeline`、`PriceCard`、`ChatPanel`、`ScanBadge`（实现位于 `src/routes/Trace.tsx` 的局部组件）。

- 移动优先 390px（max-width 430，320px 压测）；首屏是品牌/IP/批次 + 包装图 + IP 问候；随后是四 Agent 审核章、故事与引用折叠（故事区有 IP 插画时显示 768×1024 图）、包装文案、旅程/审核时间线、价格卡（档位/溢价/公式/成本）、小红书内容卡、IP 对话、扫码计数。
- 价格卡以礼盒价和溢价为 lead value；三档价格并排，公式/成本放原生 `<details>`；所有价格标“演示测算”。
- 对话：FAQ 推荐问题、用户/助手气泡、失败重试；输入框 16px 防 iOS 缩放；composer 在对话区内 `sticky bottom-0`，不遮前面内容；安全区 padding。
- 状态：首屏骨架、未知码（含 `ZTDEMO26` 入口）、网络错误重试；无横向滚动。
- 3D 联动：礼盒正/背面贴包装 PNG；内容工坊广告牌显示小红书标题；云仓二维码立牌点击打开本页；扫码数通过 `trace.scanned` 回到沙盘左栏。

## 5. 状态矩阵

| 区域 | Loading | Empty | Error | Extreme |
|---|---|---|---|---|
| 左栏 lead | 骨架块，保持高度 | “还没有批次” + 新建 | 状态获取失败 + 重试 | 批次码换行，阶段名不截断 |
| 中央 3D | 画布骨架 + 进度 | 空场景 + “新建批次” | WebGL 失败 + 静态图/重试 | DPR 上限 2，长期 60fps |
| 右栏 | 标题 + 3 行骨架 | “点一个站点开始” | Agent 失败 + 重试 + 保留内容 | 长故事 6–8 行摘要 + 展开 |
| 底部 dock | tab 骨架 | 无产出 + 运行按钮 | SSE 断线 banner + 重连 | 5 个 tab 固定，不横向溢出 |
| 审核 dialog | — | — | 保存失败保留输入 | 长文案可滚动，按钮固定底部 |
| 溯源 H5 | 首屏骨架 | 码不存在 + 返回 | 数据失败 + 重试 | 320px、长故事、长批次码 |

## 6. 七类丑自检（实现后）

| 测试 | 本项目的检查点 | 状态 |
|---|---|---|
| 1 Uncanny | 数字右对齐/tabular；主操作在预期位置；审核 dialog 主按钮在底部；关闭在右上；重置确认写出批次名 | pass（价格/扫码数 tabular；发送按钮在输入框右侧） |
| 2 Unexpected | 金额/价格用直接输入，不用 stepper；站点/批次用 peer 卡；审核用 dialog；运行按钮 100ms 内有 pressed/spinner | fixed（二维码被 Tailwind preflight 压成 14px，改 `maxWidth:none`；广告牌改用 Html 保证中文清晰） |
| 3 Detached | 原生 `<dialog>`/`<select>`；一个图标家族（lucide）；Skeleton 匹配区域；focus trap/Esc/遮罩关闭 | pass（原生 select/details/dialog；lucide 单一图标家族） |
| 4 Fragile | 压测：最长合作社名、长批次码、12 位金额、0/1/500 条产出、三行错误、320px H5、200% zoom；`min-width:0`、clamp、稳定行高 | 320px/长故事/8 条引用/长标题 pass；200% zoom 未测（known-gap） |
| 5 Unorganized | 一个 lead value + 4 个支持指标；不出现 5 张等权卡；日志/设置折叠；叙事顺序固定 | pass（价格卡 lead value；故事/包装/时间线/价格顺序固定） |
| 6 Inconsistent | token 先行；一个 Button/Input/Dialog/Card；同义操作同名；两个 radius；4/8 spacing；一个图标家族 | pass（复用全局 token 与 lucide） |
| 7 Plain ugly | 两个饱和色上限；无渐变/玻璃拟态；对比度已算；三档字号/屏；一个阴影方向；180ms 动效；真实内容/中性占位 | pass（纸感/墨绿/苹果红；无装饰渐变） |

## 7. 实现后的视觉验收

- 视口：1440×900（主）、1280×720（最低桌面）、390×844（溯源 H5）。
- 压测数据：最长合作社名“昭通市昭阳区洒渔镇乌蒙丑果专业合作社”、长批次码 `ZT-2026-001-BATCH-0001`、溢价 `156.0%`、0/1/多产出、三行错误。
- 截图检查：首屏层级、右栏溢出、底部 dock 遮挡、3D 选中标签、审核 dialog、H5 320px。
- 结果记录：每个测试写 `pass / fixed / known-gap`；没看到的不要声称通过。
- 性能：1280×720 下 60fps；DPR 上限 2；长时运行无内存增长。

## 8. 实现假设（可在 Phase 1 前调整）

- 前端栈按 plan：React + TypeScript + Vite + R3F + Zustand + Tailwind；版本在脚手架时 pin 当前稳定版，不继承旧前端的 React 18/R3F 8。
- 原生 `<dialog>` 优先；Radix 只用于 Tabs/Tooltip 这类无原生等价物的交互，不引入第二套 Dialog。
- 图标用 lucide-react；不混用 emoji/手绘系统图标。
- 不做暗色模式；不做移动端沙盘；溯源 H5 独立路由。
- 3D 构建方式对齐 WareTrack：代码拼 Box/Cylinder/Cone/Sphere/Plane 等低多边形几何体，MeshStandardMaterial + Texture 贴包装图；广告牌/二维码用 Html 覆盖层保证中文和二维码清晰；不引 GLTFLoader/外部模型；镜头正交等距、软光、暖色。
- PNG 用内置 Noto Serif/Sans；SVG 用系统字体栈；不依赖 Google Fonts CDN。

## 9. 实现状态（Phase 1 / Phase 2 / Phase 3，2026-10-22）

### Phase 1

- 已落地：token、桌面 shell、移动端 fallback、R3F 等距场景（果园/四站点/批次移动/站点状态/站点点击）、pipeline store/workspace API/SSE、工位卡、JSON 审核 dialog、产出物 Tabs、KPI、审核后自动启动下一站。
- 视觉验收：1280×720 完整 mock 流水线；390×844 溯源页与桌面端提示；无横向溢出。

### Phase 2

- 工位卡新增专用预览：故事（IP/短故事/标签）、包装（服务端 PNG + 正面/侧面/盒型）、内容（小红书/抖音钩子）、定价（溢价 + 价格梯 + 公式折叠）。
- 引用 chips：`doc_id · 标题` 外链到 `source_url`；`credibility=demo` 的条目显示“演示”，不可当事实背书；无外链的演示条目以 span + title 展示 quote。
- FactGuard 预警：琥珀色列出 rule/field/message；错误态红色；审核 dialog 顶部复用同一信息。
- 审核 dialog 保留 JSON 编辑器，增加引用/预警/包装预览；数字字段提示“服务端按定价计算器重算”。字段级表单仍未做（decisions #58）。
- API 请求加 `cache: no-store`，避免审核后仍显示旧产出；Vite dev 固定 `127.0.0.1`，与 README/代理一致。
- 视觉验收：1280×720 真实 `traced` 批次；包装卡图片、引用外链、预警列表、审核弹窗均可见；无横向溢出。

### Phase 3

- 溯源 H5：390px 单列、430px 上限；首屏包装图 + IP 问候；四 Agent 审核章；故事 + 8 条引用折叠；包装四面文案；旅程 + 审核时间线；价格卡（礼盒价/溢价/三档/公式/成本）；小红书内容卡；IP 对话 + FAQ 推荐问题；扫码计数；骨架/404/错误重试。
- 3D：礼盒正/背面贴已通过包装 PNG；内容工坊广告牌显示小红书标题；云仓二维码按钮打开 H5；批次沿 CatmullRom 路径移动；traced 后卡车驶出；左栏扫码数通过 `GET /trace/{code}/scan` 初始化并随 SSE 更新。
- 固定演示快照：`ZTDEMO26` reset 后仍有 4 条 approved run、5 条 artifact（含插画）与完整 H5；扫码/对话可用。
- 视觉验收：390×844 首屏/价格/对话截图；320px 无横向溢出；1280×720 沙盘固定演示批次截图；二维码按钮打开新标签。
- 修复：二维码被 Tailwind preflight 的 `max-width:100%` 压成 14px，改为 `maxWidth:none`；广告牌中文在 CanvasTexture 远端不可读，改用 Html 卡片；StrictMode 下提前释放纹理导致礼盒贴图空白，改用 `useTexture` + Suspense。
- Phase 3 结束时已知缺口：各 Agent 字段级表单、Playwright、200% zoom、长时 60fps/内存压测；bundle 约 1.27MB，Phase 4 拆包；包装 PNG 已内置 Noto 字体，SVG 仍依赖查看端字体，只作导出用途。

### Phase 4（已完成）

- 真实图像：包装审核通过后生成 `illustration` artifact（默认 Z-Image-Turbo，768×1024）；H5 故事区显示插画与“AI 生成演示插画 · 固定快照/服务端生成 · 非真实人物”说明；包装工位显示插画。
- 固定演示码使用 `seed/demo_illustration.png`，保留 SiliconFlow“AI 生成”水印；不把水印裁掉，避免看起来像真实摄影。
- 生图失败不阻塞审核：包装工位显示“插画生成失败，包装审核不受影响”；缓存按 prompt hash 存 `backend/data/image-cache/`。
- 包装变体：工位显示「经典牛皮纸 / 山野红 / 夜绿」色板 chips，选中后预览图、溯源图与 3D 礼盒贴图同步；只改色板，不改文案/结构/事实。
- 加载/错误/空态：路由 Suspense 骨架；`SceneBoundary` 捕获 WebGL/懒加载失败并可重试；API 错误横幅带重试；无批次时给“新建演示批次”。
- 代码分割：路由 lazy + Scene lazy；H5 不下载 three.js；`Scene` chunk 950KB 异步，initial index 260KB。
- 验证：390×844 H5 插画区截图；1280×720 包装工位插画/变体截图；2.5 秒采样 120fps；真实 API 512×512/768×1024 均 200。
- 未做：真实盒型/刀版、生图失败的视觉兜底、缓存清理（Phase 5 继续保留）。

### Phase 5（已完成）

- 自动化视觉验收：Playwright 覆盖桌面固定演示批次、包装变体/插画、3D 二维码新标签、390px H5/扫码、320px 无溢出、未知/超长码 404；视觉结构未改。
- 首次加载默认选中 `ZT-DEMO-001`（其次任一 `traced` 批次），避免现场打开落在 raw 批次。
- 插画失败兜底：包装工位在 artifact 带 `error` 或图片加载失败时显示「插画这次没有生成 / 包装审核不受影响」的设计化空态；H5 无插画 URL 或图片加载失败时省略插画区，不显示破图。
- 200% 等效视口：640×360 不挤压沙盘，回退为“3D 沙盘需要桌面端（≥1024px）”，无横向溢出；H5 仍以 320px 为最窄验收视口。
- 性能：1280×720 固定演示批次 60 秒 58.3fps，JSHeap 44.4MB→42.4MB；H5 不加载 three.js。
- 现场动线见 [runbook.md](runbook.md) §4；字段级表单确认不做，审核仍用 JSON 编辑器（decisions #58/#63）。
- 剩余视觉缺口：真实盒型/刀版。

### Phase 6（已完成）

- 顶栏「产品」下拉 + 「批次」下拉（按产品过滤）；无产品时显示“暂无产品”。
- 右侧「总控」抽屉与 `/controller` 独立页：消息气泡、流式正文、默认折叠的「思考过程」、调研草案卡、待确认卡、错误/重试、输入框。
- 总控消息区固定宽度 430px；独立页最大 720px；不挤压 3D 中栏。
- 建档/通过/驳回/回退用确认卡，不在对话里直接执行。
- 插画失败、H5 破图兜底沿用 Phase 5。
- 视觉验收：Playwright 10 条覆盖总控抽屉/独立页、用户消息乐观显示、思维链折叠、产品/批次下拉、固定演示批次、包装变体、3D 二维码、移动 H5/404。


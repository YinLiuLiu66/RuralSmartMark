# 05-probe · M0 R3F 探针报告

> 状态：✅ 完成 — 结论：**路线可行**，M3 按 5 天排
> 完成时间：2026-10-16
> 决策依据：decisions #3（纯几何体拼装）、#16（M3 依赖本探针结论）
> 代码落点：`frontend/src/three/`（probeData.ts / ProbeScene.tsx / FpsBadge.tsx）+ App.tsx

## 1. 结论

**可行，且成本远低于预期。** 程序化几何体拼装（无任何美术资源）实现"可旋转相机 +
4 站点方块 + 路径曲线 + 双车沿路径滑动 + 点击高亮 + 侧边数据卡"，全程不到一小时
（含依赖安装、编码、构建验证、浏览器实测）。原计划预留 1 天，实际显著富余。

**M3 正式 3D 沙盘按 5 天排**（原方案"探针顺利 5 天 / 受阻 10 天"，本探针未受阻）。
探针的 `src/three/` 目录结构与手势逻辑（拖拽复位、点击去误触）可直接迁入 M3 正式化。

## 2. 实测记录

| 验收项 | 结果 |
| --- | --- |
| 拖动旋转（OrbitControls） | ✅ 视角平滑变化，含阻尼惯性 |
| 滚轮缩放 | ✅ minZoom/maxZoom 约束内生效 |
| 点击站点 → 高亮 | ✅ emissiveIntensity 渐变 0.08→0.45，scale 1→1.12 |
| 点击站点 → 侧卡 | ✅ 右上角显示库存/温区/吞吐/备注，可关闭 |
| 双车沿路径匀速滑动 | ✅ CatmullRomCurve3 + getPointAt 弧长匀速 |
| 帧率 | ✅ 87–122 fps @1280×820（探针场景规模极小） |
| 路径连线 | ✅ 曲线 Line 可见；初始视角下被方块部分遮挡，旋转后可见 |

非浏览器验证：`pnpm typecheck` ✅ `pnpm lint`（oxlint）✅ `pnpm build` ✅。

## 3. 版本选型（关键踩坑点）

React 18 栈下 R3F 存在 v8/v9 分裂，**必须 pin 版本组合**：

- `three@0.169.0` + `@types/three@0.169.0`（0.169 是 drei v9 支持的上界甜点区）
- `@react-three/fiber@8.17.10`（v8 对应 React 18；**v9 强绑 React 19**，不要升）
- `@react-three/drei@9.114.3`（v9 系列兼容 fiber v8）

有 deprecated 子依赖警告（three-mesh-bvh@0.7.8，drei 传递依赖），不影响构建。
M3 正式化时如各组件升级 React 19，需整组同步迁移 fiber v9——单独升级任一包都会 typecheck 爆炸。

## 4. 实现要点（含坑）

1. **正交相机**要手动配 `position={[11, 15.5, 11]}`（仰角≈45°）+ `zoom`（46）+
   `near=-80`（正交相机 near 为负值才能不被裁切），drei 的 `<OrthographicCamera makeDefault>`。
   透视相机出不了等距沙盘感；fov 换 zoom 后视野全靠 zoom 调。
2. **连线用 drei 的 `<Line>`**（底层 meshline），原生 `<line>` 元素 lineWidth 在多数
   平台不生效，别用原生线。
3. **点击去误触**：OrbitControls 拖拽结束点落在方块上会误触发 onClick，
   必须判 `e.delta`（pointerdown→up 的位移）> 6px 时 return。探针已内置该逻辑。
4. **hover 光标**：`onPointerOver/Out` 配 `document.body.style.cursor` 即可。
   实测未观察到滑动物体（小车）干扰站点命中：R3F 事件系统按射线命中最近物体分发，
   点击站点方块中心命中稳定。站点只挂 onClick/pointer 事件即可，无需额外分层。
5. **帧率徽章**用独立 rAF 组件旁路测量（React DevTools Profiler 不适合 demo 现场），
   每秒更新一次 setState，不影响渲染循环。
6. **package 体积**：three 主包导致 build 产物 989 KB（gzip 272 KB），
   Vite 已报 chunk 大小告警。**M3 必须按页 dynamic import 懒加载三维场景**，
   溯源 H5 / 工作台页不背着 three 的体积跑。

## 5. M3 预估拆解（共 5 天）

| 天 | 内容 |
| --- | --- |
| D1 | 搭真实场景骨架：按 03 文档站点/场地模型摆位 + 地面装饰（低-poly 农田/仓库体块） |
| D2 | 吃 REST 快照 `/api/world/snapshot` 渲染 13 表现势数据（decisions #17） |
| D3 | 吃 WS 增量 `/ws/world`：托盘位移/车辆移动/站点状态实时更新（decisions #15/#17/#19） |
| D4 | 交互细化：站点/车辆/托盘三类点击卡 + 选中物 track（Zustand, decisions #8） + 路径流光 |
| D5 | 打磨 + 三档画质档位验证 + 降级触发点检查（2.5D SVG 路线备用） + 演示动线预演 |

依赖前置：D2/D3 需要 M2 sim 引擎 + WS 可用；D1–D4 并行期用探针假数据先行可行（decisions #16）。

## 6. 探针代码去向

`frontend/src/three/` 三份文件保留为主体迁入 M3（不删；探针数据文件 probeData.ts
在 M3 后被 REST/WS 数据源替换，但站点元数据结构可复用）。App.tsx 探针壳届时替换为路由页。

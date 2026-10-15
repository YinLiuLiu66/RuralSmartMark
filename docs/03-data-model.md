# 03 · 数据模型与接口约定

> 状态：🔶 草案 — 实体清单已定，字段细节随开发补充
> 更新时间：2026-10-14

## 1. 核心实体（约 12 张表）

仿 WareTrack 的对象模型：六类运行时实体 + Agent/业务实体。

### 运行时实体（模拟引擎持续更新）

| 表 | 说明 | 关键字段（草案） |
| --- | --- | --- |
| `cooperative` | 合作社/主体 | name, contact |
| `site` | 站点（集货仓/前置仓） | type(origin_hub / forward_warehouse), capacity, status |
| `vehicle` | 冷链车 | plate, status(en_route/docking/unloading/departed), temperature, humidity |
| `worker` | 分拣/月台人员 | site_id, name, status, moves_today |
| `pallet` | 托盘/礼盒货位 | sku_id, site_id, qty, batch_no |
| `shipment` | 运单（五步状态机） | from_site, to_site, vehicle_id, status stepper |

### Agent/业务实体

| 表 | 说明 | 关键字段（草案） |
| --- | --- | --- |
| `product_sku` | IP 礼盒品类 | name, story_id, base_price, brand_price |
| `telemetry` | 冷链温湿度 | vehicle_id, ts, temperature, humidity（滚动窗口） |
| `agent_task` | Agent 任务 | agent_type, status, product_sku_id, created_by |
| `agent_artifact` | Agent 产出物 | task_id, kind(story/copy/design), content, status(draft/polished/final) |
| `trace_code` | 一物一码 | code, pallet_id, shipment_id, activated_at |
| `price_benchmark` | 溢价对照 | sku_id, channel, base_price, brand_price, premium_rate |

**关系要点**：

- `shipment` 串联 `site`/`vehicle`/`pallet`，是溯源时间线的数据源
- `trace_code` 是消费者扫码入口，联到 `pallet` + `shipment` 的历史
- `agent_artifact` 状态流转支撑"AI 初稿 → 人工润色 → 定稿"演示

## 2. 运单（shipment）五步状态机

```
Order Confirmed → Picked → Loading/Loaded → In Transit → Delivered/Unloading
```

模拟引擎按剧本推进各运单状态，前端 stepper 展示。

## 3. 接口约定

所有业务接口统一挂在 `/api` 前缀下（沿用现有 README 的约定），WebSocket 走 `/ws`。

### 3.1 已实现

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 ✅ |

### 3.2 规划（随开发补充，本表为骨架）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/token` | 登录换 JWT（双角色） |
| GET | `/api/world/snapshot` | 沙盘全量快照（3D 场景初始化用） |
| GET | `/api/sites` / `/api/vehicles` / ... | 运行时实体查询 |
| GET | `/api/shipments/{id}` | 运单详情（含 stepper + 事件时间线） |
| WS | `/ws/world` | 沙盘实时事件流（快照+增量，模拟时钟 tick） |
| POST | `/api/agent-tasks` | 发起 Agent 任务（story/copy/...） |
| GET | `/api/agent-tasks` | 任务列表（工作台用） |
| PATCH | `/api/agent-artifacts/{id}` | 人工润色产出物 |
| GET | `/api/trace/{code}` | 扫码溯源数据（公开接口，无需鉴权） |
| GET | `/api/pricing/benchmarks` | 溢价对照数据 |

### 3.3 WebSocket 事件类型（草案）

```
tick.info           # 模拟时钟推进（虚拟时间、速度）
entity.updated      # 实体状态变更（车辆/站点/托盘）
shipment.progressed # 运单进入下一步
agent.task_updated  # Agent 任务状态/进度
agent.artifact_ready# Agent 产出物就绪
scheduler.proposal  # Agent 5 的调度建议
```

## 4. 待定问题

- [ ] 表字段具体化（随 Alembic 首次迁移前定稿）
- [ ] WebSocket 是否需要按角色区分推送内容（游客/运营方看到的范围）
- [ ] `trace_code` 的码格式与批量生成方式

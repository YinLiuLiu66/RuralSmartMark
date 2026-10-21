# 03 · 数据模型与接口约定

> 状态：✅ 主干定稿 — 实体与字段已按 decisions #15–#19 收口；M2 亮出快照/控制/WS，M4 增加 Agent 任务与产出物接口，M5 增加公开溯源接口，M6 增加公开溢价对照接口
> 更新时间：2026-10-21

## 1. 核心实体（约 12 张表）

仿 WareTrack 的对象模型：六类运行时实体 + Agent/业务实体。

### 运行时实体（模拟引擎持续更新）

| 表 | 说明 | 关键字段（草案） |
| --- | --- | --- |
| `cooperative` | 合作社/主体 | name, contact |
| `site` | 站点（集货仓/前置仓） | type(origin_hub / forward_warehouse), capacity, status |
| `vehicle` | 冷链车 | plate, status(en_route/docking/unloading/departed), temperature, humidity |
| `worker` | 分拣/月台人员 | site_id, name, status, moves_today |
| `pallet` | 托盘/礼盒货位 | sku_id, qty, batch_no, current_site_id / current_vehicle_id（现势字段，沙盘读） |
| `shipment` | 运单（五步状态机） | from_site, to_site, vehicle_id, status stepper |
| `trace_event` | 溯源事件流水 | pallet_id, ts, kind(harvested/packed/stored/loaded/departed/arrived/unloaded/delivered/temp_alert), payload_json；append-only，模拟引擎关键节点写入（decisions #15） |

### Agent/业务实体

| 表 | 说明 | 关键字段（草案） |
| --- | --- | --- |
| `product_sku` | IP 礼盒品类 | name, story_id, box_price（礼盒定价；散装行情只存 price_benchmark，溢价率保持单一算法） |
| `telemetry` | 冷链温湿度 | vehicle_id, ts, temperature, humidity（滚动窗口） |
| `agent_task` | Agent 任务 | agent_type, status, product_sku_id, created_by |
| `agent_artifact` | Agent 产出物 | task_id, kind(story/copy/design), content, asset_url（图片资产挂静态目录，Agent 2 用）, status(draft/polished/final) |
| `trace_code` | 一物一码 | code（8 位 Base32 大写随机码，无歧义字符，URL 安全）, pallet_id（唯一锚点）, activated_at |
| `price_benchmark` | 溢价对照 | sku_id, channel, bulk_price（该渠道散装行情价）, brand_price（礼盒成交价）, premium_rate；M6 三档演示测算（decisions #31） |

**关系要点**：

- `shipment` 串联 `site`/`vehicle`/`pallet`；溯源时间线的数据源是 `trace_event` 流水（全库模式：现势存实体表，历史存事件表，见 decisions #15）
- `trace_code` 是消费者扫码入口，只锚 `pallet`；时间线按 `pallet_id` 查流水，在途温度按运单时段查 `telemetry`
- `agent_artifact` 状态流转支撑"AI 初稿 → 人工润色 → 定稿"演示

## 2. 运单（shipment）五步状态机

```
Order Confirmed → Picked → Loaded → In Transit → Delivered
```

模拟引擎按剧本推进各运单状态，前端 stepper 展示。`Picked` 定义为提货离仓（集货仓侧）。
**要点**：状态机只供沙盘 stepper；溯源时间线不直接消费运单状态，而读 `trace_event` 流水（卸货、温湿度异常等细粒度动作在那里落事件，见 decisions #15）。

## 3. 接口约定

所有业务接口统一挂在 `/api` 前缀下（沿用现有 README 的约定），WebSocket 走 `/ws`。

### 3.1 已实现

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 ✅ |
| POST | `/api/auth/token` | 登录换 JWT（双角色，M1）✅ |
| GET | `/api/auth/me` | 身份探针（M1 验收用）✅ |
| POST | `/api/sim/control` | 模拟时钟控制 pause/resume/speed/reset，限运营方（M2，decisions #17）✅ |
| GET | `/api/world/snapshot` | 沙盘全量快照：时钟 + 站点/车辆/工人/托盘/运单现势 + 在途路线（M2）✅ |
| WS | `/ws/world` | 增量事件流：tick.info / entity.updated / shipment.progressed / world.reset（M2，不鉴权）✅ |
| POST | `/api/agent-tasks` | 发起 Agent 任务（story/copy），后台生成（M4，decisions #26）✅ |
| GET | `/api/agent-tasks` | 任务列表（工作台用）✅ |
| GET | `/api/agent-tasks/{id}` | 单任务详情 ✅ |
| PATCH | `/api/agent-artifacts/{id}` | 编辑 / 润色 / 定稿（M4，decisions #25）✅ |
| GET | `/api/agent-artifacts/{id}` | 单产出物 ✅ |
| GET | `/api/trace/{code}` | 扫码溯源（公开，无需鉴权）：产品/批次 + 最新 final 品牌故事 + `trace_event` 时间线（M5，decisions #30）✅ |
| GET | `/api/pricing/benchmarks` | 溢价对照（公开，无需鉴权）：三档渠道散装价 vs 礼盒价 + 溢价率（M6，decisions #31，演示测算）✅ |

### 3.2 规划（随开发补充）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/sites` / `/api/vehicles` / ... | 运行时实体查询（按需加；当前快照接口已覆盖） |
| GET | `/api/shipments/{id}` | 运单详情（含 stepper + 事件时间线） |

### 3.3 WebSocket 事件类型

已实现（M2）：`tick.info`（模拟时钟推进，含控制动作后的状态）、`entity.updated`
（车辆 / 工人 / 托盘现势变化）、`shipment.progressed`（运单沿五步推进）、
`world.reset`（重置通知，客户端收到后重拉快照）。

已实现（M4）：`agent.task_updated`（任务状态变化，data 为完整任务）、
`agent.artifact_ready`（产出物就绪）。规划：`scheduler.proposal`（Agent 5 的调度建议）。

> 增量事件封套统一为 `{type, sim_time, data}`；全量快照走
> `GET /api/world/snapshot`，WS 不推快照（decisions #17）；推送不区分角色（#19）。

## 4. 权限矩阵（M1 JWT 规格）

| 角色 | 权限 |
| --- | --- |
| 运营方 | sim 时钟控制、Agent 任务发起、产出物编辑/润色/定稿、全部查询（#25） |
| 合作社 | 发起 Agent 任务、编辑自己草稿、全部查询（#25） |
| 公开 | `GET /api/trace/{code}`（无需鉴权） |

## 5. 待定问题

- [ ] 表字段细节随 Alembic 首版迁移最终落定（主干已按 decisions #15–#19 收口；WS 推送已定不区分角色，见 #19）

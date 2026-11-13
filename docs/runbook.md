# v2 Runbook · 启动、演示、验收

> 适用：2026-10-22 后的 main。环境与命令以根 [AGENTS.md](../AGENTS.md) 为准；本文只写操作顺序和现场口径。

## 1. 首次准备

```bash
cd backend && uv sync && cd ..
cd frontend && pnpm install && pnpm exec playwright install chromium && cd ..
cp backend/.env.example backend/.env   # 已有 .env 则跳过
```

- `OPENAI_API_KEY` 可空；空则走 mock，四站仍能跑通。
- 总控真实调研需要 `FIRECRAWL_API_KEY`；没有 key 时总控会提示贴来源，不会编资料。
- 前端 Playwright Chromium 下载到 `~/Library/Caches/ms-playwright`，不入仓库。
- 不要提交 `backend/.env`、`backend/data/`、`frontend/dist/`、`frontend/test-results/`。

## 2. 启动

```bash
make dev
```

等价于：后端迁移 + 幂等 seed + 起 8000，前端起 5173。打开 http://127.0.0.1:5173 。

单独启动：

```bash
cd backend && uv run alembic upgrade head && uv run python -m ruralsmartmark.seed && uv run ruralsmartmark
cd frontend && pnpm dev
```

### 2.1 手机真机扫码（局域网）

```bash
make lan
```

- 电脑与手机连同一个 Wi-Fi；脚本会打印 `http://<局域网IP>:5173/trace/ZTDEMO26`，3D 二维码和包装二维码都指向这个地址。
- 首次运行 macOS 可能弹防火墙提示，允许 Python/Node 接入局域网。
- 只用于可信局域网；默认 `make dev` 仍只绑 `127.0.0.1`。Ctrl-C 会一起停前后端。
- IP 变了（切换 Wi-Fi/热点）就重新 `make lan`；脚本会重新 seed + reset，二维码跟着更新。

### 2.2 总控 / 新产品

- 打开 `http://127.0.0.1:5173/` 是**工作台**：每个项目一张卡（昭通丑苹果、麻江蓝莓），点卡进沙盘；右上「总控」打开常驻抽屉，或「全页聊天」进 `/controller`。
- 总控是**全局一段会话**：从工作台、项目页、全页聊天切来切去，对话和记忆都是同一段；它根据当前页面知道你在哪个项目/批次/站点。
- 输入“帮我做一个新产品，我想做贵州麻江蓝莓”，总控会搜索/追问并生成档案草案。发送后用户消息立即出现；回答逐字流式增长，点「思考过程」展开思维链（默认折叠）。
- 草案出齐后，在确认卡点「确认建档」；建档成功会自动回工作台，新卡片出现。
- 在项目页说“运行故事”“包装改克制一点”“通过故事”“回到包装重做”。
- 说“审核通过”会先出确认卡，卡上写明目标批次；确认后通过并自动运行下一站。
- 在工作台或 `/controller` 直接说“通过”会**反问哪个批次**并给候选，这是预期行为：没有页面批次就不猜。
- 建档/通过/驳回/回退都会先弹确认卡；查资料/读状态不会。
- 真实搜索需要 Firecrawl key；没有 key 时贴官网/报道链接或原文。检索连接中断会自动重试，仍失败时直接贴链接即可。

## 3. 固定演示数据

- 演示批次 `ZT-DEMO-001`，溯源码 `ZTDEMO26`，四章产出 + 5 个 artifact（含 IP 插画）。
- 重置：

```bash
curl -X POST http://127.0.0.1:8000/api/demo/reset
```

- reset 幂等：重复调用不会产生重复 run/artifact；扫码数归零；`ZTDEMO26` 内容不变。
- seed 现在带两个项目：昭通丑苹果（`ZT-DEMO-001` traced + `ZT-2026-001` raw）与麻江蓝莓（`MJ-2026-001` raw）。项目页默认选该产品下**已 traced** 的批次，否则取第一条；批次 id 会写进 URL 的 `?batch=`。

## 4. 现场演示动线（约 5 分钟）

1. **工作台**：打开 `/`，指出这是产品集合：昭通丑苹果已 6/6、麻江蓝莓刚建档 0/6。「换产品只换档案，不换代码」。
2. **进沙盘**：点昭通卡进入 `/project/zhaotong-ugly-apple`，指出 6/6 已完成、品牌护照、四站点状态；拖动/缩放 3D，说明低多边形是程序化几何，不是 GLB。
3. **包装工位**：点右侧「包装设计」或 3D 包装站；切换「经典牛皮纸 / 山野红 / 夜绿」，指出 3D 贴图同步；展示 IP 插画并说明是 Z-Image-Turbo 生成、固定演示码用快照。
4. **扫码闭环**：点 3D 二维码立牌（或底部「溯源」），打开 `/trace/ZTDEMO26`；说明 390px H5、四段审核章、价格公式与“演示测算”标注。
5. **H5 细节**：故事与引用、包装文案、旅程/审核时间线、小红书卡；问守园人一个保守问题（如“怎么保存？”），说明认证/功效类问题会被拒答。
6. **回沙盘**：指出扫码数随 `trace.scanned` 增加；如时间充足，回工作台点麻江蓝莓，现场跑故事站（会消耗真实 LLM 额度，先确认网络与 key），证明“换个产品真能跑”。
7. **总控**：打开右侧「总控」，说“我有哪些项目”“现在到哪了”；在工作台直接说“通过”，展示它会反问批次并给候选，说明不会打错批次。
8. **收尾**：`curl -X POST .../api/demo/reset` 恢复干净演示态。

## 5. 验收命令

```bash
make test    # 后端 106 passed + 2 skipped + ruff；前端 typecheck/lint/build
make e2e     # Playwright 15 条冒烟（桌面 10 + 移动 5）
make perf    # 60 秒帧率/堆内存 + 移动端帧率 + 640×360 窄视口
cd backend && RSM_REAL_LLM=1 uv run pytest tests/test_second_product_real.py  # 可选，真实 LLM 会消耗额度
cd backend && RSM_REAL_SEARCH=1 uv run pytest tests/test_search_real.py  # 可选，真实 Firecrawl 会消耗 credits
cd backend && uv run python -m ruralsmartmark.maintenance image-cache --dry-run  # 缓存清理预演
```

- 性能基线（2026-10-22，本机 1280×720 headless Chromium）：60 秒 58.3fps，JSHeap 44.5MB→42.4MB。
- 200% 等效视口（640×360）不挤沙盘，显示“3D 沙盘需要桌面端（≥1024px）”，无横向溢出。
- H5 320px 视口无横向溢出；超长溯源码走 404 面板。

## 6. 新增一个产品档案

第二产品是 canonical 数据：`backend/src/ruralsmartmark/seed/products/majiang/`（`product.json` + `benchmarks.json` + `knowledge/`）。seed 与测试共用这一份，不要再复制到 `tests/fixtures/`。

1. 新建知识库目录，Markdown frontmatter 必须含 `id/title/type/source_url/source_date/credibility`；演示产品全部标 `credibility: demo`。
2. 准备产品 JSON：`slug/name/county/category/form/specs/palette/knowledge_dir`；`specs` 至少含 `brand_name/ip_name/batch_prefix/trace_prefix`，可选 `agent_context/brand_rule/*_brief/pack_kg/*_pack_label/packaging_hero/packaging_tagline/trace_footer/pricing_faq/demo_copy`。
3. 准备 3 条基准价（散装批发 / 电商散装 / 品牌礼盒，元/kg）；定价计算器需要 `PRICE-01` 与 `DEMO-01` 两篇文档。
4. 在 `seed/__init__.py` 的 `seed_products()` 里加一条 `ProductSeed`；批次停在 `raw` 即可现场演示跑站。不需要改 Agent、编排器、定价、包装或 H5 代码。
5. 参考测试：`backend/tests/test_second_product.py`（断言 `traced`、`MJ` 溯源码、公开 H5、包装 PNG、无昭通/苹果残留）。
6. 可选真实 LLM 冒烟：`cd backend && RSM_REAL_LLM=1 uv run pytest tests/test_second_product_real.py`。会消耗额度，默认跳过。

## 7. 故障排查

| 现象 | 处理 |
|---|---|
| 右上“后端未连接” | 确认 8000 在跑；`curl http://127.0.0.1:8000/api/health`；看 `backend` 终端错误 |
| 顶栏“重连中” | SSE 断线会自动重连；仍不恢复则刷新页面重拉 workspace |
| 3D 显示“场景没有启动” | 点“重试 3D”；确认浏览器 WebGL 未禁用；移动端沙盘为简化布局（#93） |
| 包装工位没有图 | 先确认选中 `ZT-DEMO-001`；再看 `/api/trace/ZTDEMO26/packaging.png` 是否 200 |
| 总控说“需要指定目标” | 预期行为：工作台/全页聊天没有页面批次，写操作要反问。点候选 chip 或进项目页再说 |
| 插画生成失败 | 审核不受影响；检查 `IMAGE_*` 配置与网络，重跑包装或稍后重试 |
| 总控发消息后一直“思考中” | 看后端日志与 `/api/controller/sessions/{id}/messages/stream` 是否在建连；检查 `CONTROLLER_REQUEST_LIMIT`、模型超时与网络；刷新后消息仍在，可重发 |
| 总控没有思维链 | 确认 `LLM_THINKING_BUDGET>0`；短回答模型可能不产生 reasoning，属正常；思考过程默认折叠，点“思考过程”展开 |
| Firecrawl 检索报连接中断 | 默认 `FIRECRAWL_TRUST_ENV=false` 绕过本地系统代理；仍失败时检查 key/额度，或直接贴来源链接/原文 |
| Playwright 报浏览器缺失 | `cd frontend && pnpm exec playwright install chromium` |
| 端口被占用 | 停掉旧进程；Playwright `reuseExistingServer` 会复用已跑的 8000/5173 |

## 8. 现场边界

- 固定演示码依赖 seed 快照，不依赖现场 LLM/图像 API；断网也能打开 H5。
- 价格、成本、溢价均为演示测算；品牌、IP、合作社为演示合成；区域事实引用知识库。
- 地理标志公告号与 80–85mm 公开挂牌价已补；包装厂只有 1000 个起订线索，无书面报价；手机真机扫码、真实盒型/刀版仍未做。
- 不做字段级审核表单、Docker、真实盒型/刀版、真实供应商报价；详见 [decisions.md](decisions.md) #58/#63/#64。

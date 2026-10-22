# 智农云链 v2 · backend

FastAPI + SQLAlchemy 2.0 + SQLite。无需 Docker/Postgres。

```bash
cd backend
cp .env.example .env          # 首次；把 OPENAI_API_KEY 填上（不填则走 mock）
uv sync
uv run alembic upgrade head
uv run python -m ruralsmartmark.seed
uv run ruralsmartmark         # http://127.0.0.1:8000
```

测试与检查（52 条常跑 + 2 条可选真实外部冒烟）：

```bash
uv run pytest
RSM_REAL_LLM=1 uv run pytest tests/test_second_product_real.py   # 可选，会消耗额度
RSM_REAL_SEARCH=1 uv run pytest tests/test_search_real.py         # 可选，真实 Firecrawl credits
uv run ruff check .
uv run ruff format .
uv run python -m ruralsmartmark.maintenance image-cache --dry-run  # 生图缓存清理预演
```

接口：

- `GET /api/health`
- `GET /api/products` / `GET /api/knowledge`
- `GET /api/batches?product_id=`
- `POST /api/batches`（body: `{"product_slug": "zhaotong-ugly-apple", "quantity_kg": 300}`）
- `GET /api/batches/{id}` / `GET /api/batches/by-code/{code}`
- `GET /api/batches/{id}/workspace`；`POST /api/batches/{id}/pipeline/start`
- `POST /api/batches/{id}/agents/{agent}/run|approve|reject`
- `GET /api/batches/{id}/agents/packaging/preview`（服务端 PNG，`?variant=`）
- `GET /api/batches/{id}/agents/packaging/variants`（包装变体清单）
- `GET /api/artifacts/{id}/file`（审核后的 PNG）
- `GET /api/batches/{id}/events`（SSE）
- `GET /api/trace/{code}` / `packaging.png` / `qr.png`
- `GET|POST /api/trace/{code}/scan`；`POST /api/trace/{code}/chat`
- `POST /api/controller/sessions` / `GET /api/controller/sessions/{id}`
- `POST /api/controller/sessions/{id}/messages` / `confirm`（总控调研/运行/确认）
- `POST /api/demo/reset`（重建固定演示批次并保留完整内容）

知识库在仓库根 `data/knowledge/zhaotong/*.md`，seed 时写入 `knowledge_doc`；`seed/demo_batch.json` 是固定演示批次的真实 V4.1 内容快照，`seed/demo_illustration.png` 是对应 IP 插画快照；reset 后由 seed 写入四章产出、4 条 approved run、5 条 artifact（含插画）和确定性定价。真实 LLM 可空 key 走 mock；`LLM_FALLBACK_TO_MOCK` / `LLM_TIMEOUT_SECONDS` / `LLM_THINKING_BUDGET` / `LLM_MAX_TOKENS` 见 `.env.example`；默认模型 `deepseek-ai/DeepSeek-V4.1-Flash`。

图像：`providers/image.py` 调 SiliconFlow `POST /v1/images/generations`，默认 `IMAGE_MODEL=Tongyi-MAI/Z-Image-Turbo`（可切 `Tongyi-MAI/Z-Image`）；`IMAGE_SIZE` 空时按 512×512 / 1024×576 / 768×1024 自动选择；生成结果缓存到 `backend/data/image-cache/`（已 gitignore）。包装审核通过后生成 `illustration` artifact，失败只记录错误，不阻塞审核。SQLite 文件默认在 `backend/data/app.db`（已 gitignore）。

第二产品夹具仍在 `tests/fixtures/majiang/`，用于验证档案化；运行期多产品由总控建档写入。提示词、mock 文案、定价标签、包装品牌字、溯源码前缀均从 `ProductProfile.specs` 读取；`RSM_REAL_LLM=1` 时 `tests/test_second_product_real.py` 用真实 V4.1-Flash 跑四站，默认跳过以免扣费。

总控调研依赖 `pydantic-ai-slim[openai]` 与 `firecrawl-py`，只装在本项目 venv；`FIRECRAWL_API_KEY` 空时提示贴资料。`docs/v2/plan.md` 是当前方案，`docs/v2/controller.md` 是总控契约，`docs/v2/runbook.md` 是启动与演示操作。

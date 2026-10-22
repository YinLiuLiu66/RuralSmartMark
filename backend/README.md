# 乡土印记 v2 · backend

FastAPI + SQLAlchemy 2.0 + SQLite。无需 Docker/Postgres。

```bash
cd backend
cp .env.example .env          # 首次；把 OPENAI_API_KEY 填上（不填则走 mock）
uv sync
uv run alembic upgrade head
uv run python -m ruralsmartmark.seed
uv run ruralsmartmark         # http://127.0.0.1:8000
```

测试与检查：

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

接口：

- `GET /api/health`
- `GET /api/products` / `GET /api/knowledge`
- `GET /api/batches`
- `POST /api/batches`（body: `{"product_slug": "zhaotong-ugly-apple", "quantity_kg": 300}`）
- `GET /api/batches/{id}` / `GET /api/batches/by-code/{code}`
- `GET /api/batches/{id}/workspace`；`POST /api/batches/{id}/pipeline/start`
- `POST /api/batches/{id}/agents/{agent}/run|approve|reject`
- `GET /api/batches/{id}/agents/packaging/preview`（SVG）
- `GET /api/artifacts/{id}/file`（审核后的 PNG）
- `GET /api/batches/{id}/events`（SSE）
- `POST /api/demo/reset`

知识库在仓库根 `data/knowledge/zhaotong/*.md`，seed 时写入 `knowledge_doc`。真实 LLM 可空 key 走 mock；`LLM_FALLBACK_TO_MOCK` / `LLM_TIMEOUT_SECONDS` / `LLM_THINKING_BUDGET` / `LLM_MAX_TOKENS` 见 `.env.example`；默认模型 `deepseek-ai/DeepSeek-V4.1-Flash`。SQLite 文件默认在 `backend/data/app.db`（已 gitignore）。`docs/v2/plan.md` 是当前方案。

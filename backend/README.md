# RuralSmartMark Backend

FastAPI 服务端。运行说明见仓库根目录 [README](../README.md)。

## 快速开始

```bash
cd backend
uv sync
cp .env.example .env   # 按需填写
uv run ruralsmartmark
```

服务默认监听 `http://127.0.0.1:8000`，交互式文档在 `/docs`。

## 常用命令

| 目的 | 命令 |
| --- | --- |
| 启动开发服务 | `uv run ruralsmartmark` |
| 运行测试 | `uv run pytest` |
| 代码检查 | `uv run ruff check .` |
| 格式化 | `uv run ruff format .` |

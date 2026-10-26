# v2 生产部署 · Linux 单机（nginx + systemd）

> 适用：把「智农云链」部署到一台 Linux 服务器，供桌面沙盘、总控和手机扫码 H5 使用。
> 本机开发、演示动线、新增档案、排障见 [runbook.md](runbook.md)；本文只写服务器部署。
> 决策依据：[decisions.md](../decisions.md) #63（不做 Docker）、#90（nginx + systemd 单进程）。

## 0. 边界与验证状态

- **形态**：单机、单进程 uvicorn、SQLite 单文件；nginx 托管前端静态文件并反代 `/api`。
- **不做**：Docker / 容器编排（#63）、多 worker / 水平扩展、对象存储、CDN、应用层登录（红线）。
- **资源**：2 核 2G 起；磁盘 ≥ 2GB（依赖 + 39MB 内置字体 + 运行产物）。SQLite 单写，适合演示与小团队，不适合高并发多租户。
- **出网**：服务器需能访问 SiliconFlow（LLM/生图）与 Firecrawl；无 key 时走 mock，但总控调研会退化为“贴资料”。
- **验证状态（2026-10-26）**：前端 `pnpm build` 与后端 `APP_ENV=production DEBUG=false` 启动、`/api/health` 200 已在本机 macOS 实测；`backend/data` 缺失时迁移报 `unable to open database file` 也已实测。**nginx 与 systemd 配置尚未在目标服务器执行**，首次上线请按 §9 逐项验收；手机真机扫码仍未实测（见 runbook §2.1）。

## 1. 目录与用户

以下路径统一假设仓库在 `/opt/ruralsmartmark`，运行用户为 `rsm`；换成自己的路径时同步改 nginx 与 systemd。

```bash
sudo useradd --create-home --shell /bin/bash rsm
sudo mkdir -p /opt/ruralsmartmark
sudo chown rsm:rsm /opt/ruralsmartmark
sudo -H -u rsm git clone <repo-url> /opt/ruralsmartmark
```

必须从 **git 源码树**部署，不要只装 wheel：知识库按仓库根目录解析（`services/knowledge.py`），seed 依赖 `data/knowledge/zhaotong/*.md`。

## 2. 依赖

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| Python | 3.13 | 后端（`requires-python >=3.13`） |
| uv | ≥ 0.13 | 安装后端依赖、管理 `.venv` |
| Node | ≥ 20.19（本机实测 24.22.1） | 只在服务器构建前端时需要 |
| pnpm | ≥ 10（本机实测 12.14.0） | 同上 |
| nginx | 任意稳定版 | 静态文件 + 反代 |
| certbot | 可选 | HTTPS |

只构建一次前端的话，Node/pnpm 可以只装在本地，把 `dist/` 传上去（§5）。

```bash
# uv 装到 /usr/local/bin，rsm 用户可直接调用
curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin sh
# 让 uv 把 Python 3.13 装进 rsm 的 HOME（不要用 root 装，否则 rsm 找不到）
sudo -H -u rsm uv python install 3.13
```

> 下文的 `sudo -H -u rsm` 会切到 `rsm` 的 HOME，避免 uv 缓存与解释器落到 root 名下；漏掉 `-H` 常见的后果是 `Permission denied` 或 uv 反复下载 Python。

## 3. 后端安装与配置

```bash
sudo -H -u rsm mkdir -p /opt/ruralsmartmark/backend/data
cd /opt/ruralsmartmark/backend
sudo -H -u rsm uv sync --frozen --no-dev
sudo -H -u rsm cp .env.example .env
sudo -H -u rsm chmod 600 .env
```

`backend/data/` 必须先建：它被 `.gitignore` 排除，新 clone 没有这个目录，`alembic upgrade head` 会直接失败。

编辑 `backend/.env`，至少改这些：

| 变量 | 生产值 | 说明 |
| --- | --- | --- |
| `APP_ENV` | `production` | |
| `DEBUG` | `false` | example 默认 `true` 会开 uvicorn reload |
| `HOST` | `127.0.0.1` | 只给 nginx 反代，不对公网监听 |
| `PORT` | `8000` | |
| `DATABASE_URL` | `sqlite+aiosqlite:////opt/ruralsmartmark/backend/data/app.db` | **用绝对路径**；example 里的 `./data/app.db` 是相对 CWD 的 |
| `PUBLIC_BASE_URL` | `https://你的域名` | 二维码、包装 PNG、H5 链接都取这个值；不要带结尾 `/` |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | 按实际 | 空 key = mock 模式 |
| `IMAGE_MODEL` / `IMAGE_BASE_URL` / `IMAGE_SIZE` | 按实际 | 空 `IMAGE_BASE_URL` 复用 LLM 端点 |
| `FIRECRAWL_API_KEY` | 按实际 | 总控真实检索；空则提示贴资料 |
| `AUTO_APPROVE` | `false` | 保留人工审核门 |
| `LLM_TIMEOUT_SECONDS` | `180` | 营销长文实测需要 |
| `LLM_FALLBACK_TO_MOCK` | `true` | 真实调用失败时降级，不阻塞演示 |

同源部署（nginx 同时发前端和 `/api`）不需要改 `CORS_ORIGINS`；前后端分属不同域名时，把 `CORS_ORIGINS` 改成前端完整 origin（不要用 `*`，后端开了 `allow_credentials`）。

初始化数据库与演示数据：

```bash
cd /opt/ruralsmartmark/backend
sudo -H -u rsm .venv/bin/alembic upgrade head
sudo -H -u rsm .venv/bin/python -m ruralsmartmark.seed
```

`PUBLIC_BASE_URL` 必须在 seed **之前**定好：固定演示批次的 `pricing_json.trace_url` 会在 seed 时烘进去。之后改域名要重跑 `POST /api/demo/reset`（或直接重新 seed）才会更新；二维码图片和包装 PNG 是请求时渲染的，会立即跟着变。

## 4. 前端构建

产物 `frontend/dist/` 约 1.3MB，`dist/` 被 gitignore，不随仓库走。

在服务器构建：

```bash
cd /opt/ruralsmartmark/frontend
sudo -H -u rsm pnpm install --frozen-lockfile
sudo -H -u rsm pnpm build
```

或在本地构建后同步（服务器不需要 Node）：

```bash
cd frontend && pnpm build
rsync -a --delete dist/ <user>@<server>:/opt/ruralsmartmark/frontend/dist/
ssh <user>@<server> 'sudo chown -R rsm:rsm /opt/ruralsmartmark/frontend/dist'
```

## 5. systemd

`/etc/systemd/system/ruralsmartmark.service`：

```ini
[Unit]
Description=智农云链后端 (FastAPI)
After=network.target

[Service]
Type=simple
User=rsm
Group=rsm
WorkingDirectory=/opt/ruralsmartmark/backend
Environment=APP_ENV=production
Environment=DEBUG=false
Environment=HOST=127.0.0.1
Environment=PORT=8000
ExecStart=/opt/ruralsmartmark/backend/.venv/bin/uvicorn ruralsmartmark.main:app \
    --host 127.0.0.1 --port 8000 --workers 1 --proxy-headers
Restart=on-failure
RestartSec=3
KillSignal=SIGINT
TimeoutStopSec=20
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ReadWritePaths=/opt/ruralsmartmark/backend/data

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ruralsmartmark
sudo systemctl status ruralsmartmark
curl -fsS http://127.0.0.1:8000/api/health   # {"status":"ok","app":"ruralsmartmark-v2","db":"ok"}
```

**`--workers` 必须是 1。** 流水线 SSE 的事件总线是进程内存（`services/events.py`），总控流式用 `asyncio.create_task`（`routes/controller.py`）；多 worker 会丢事件、同一会话请求落到不同进程。不要用 `uv run` 启动（unit 里直接用 venv 的 uvicorn 更稳）；密钥与模型配置放 `.env`，unit 只覆盖运行模式。

日志：`journalctl -u ruralsmartmark -f`。

## 6. nginx

### 6.1 公共反代片段

`/etc/nginx/snippets/rsm-proxy.conf`：

```nginx
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Connection "";

# SSE 与长请求：不缓冲、超时大于 LLM_TIMEOUT_SECONDS
proxy_buffering off;
proxy_cache off;
proxy_read_timeout 600s;
proxy_send_timeout 600s;
```

### 6.2 站点配置

`/etc/nginx/sites-available/ruralsmartmark`：

```nginx
server {
    listen 80;
    server_name example.com;   # 换成你的域名或公网 IP

    root /opt/ruralsmartmark/frontend/dist;
    index index.html;

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
    gzip_min_length 1024;

    # 构建产物带 hash，可长缓存
    location ^~ /assets/ {
        try_files $uri =404;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # 公开：手机扫码 H5。前端是 BrowserRouter，必须回退到 index.html
    location ^~ /trace/ {
        try_files $uri /index.html;
    }

    # 公开：H5 调用的溯源 API（含 chat / scan / qr.png / packaging.png）
    location ^~ /api/trace/ {
        include snippets/rsm-proxy.conf;
        proxy_pass http://127.0.0.1:8000;
    }

    # 管理端 API：无应用层鉴权，公网必须在外层保护
    location /api/ {
        auth_basic "智农云链";
        auth_basic_user_file /etc/nginx/.htpasswd;

        include snippets/rsm-proxy.conf;
        proxy_pass http://127.0.0.1:8000;
    }

    # 管理端页面：沙盘 / 总控
    location / {
        auth_basic "智农云链";
        auth_basic_user_file /etc/nginx/.htpasswd;

        try_files $uri /index.html;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ruralsmartmark /etc/nginx/sites-enabled/
sudo htpasswd -c /etc/nginx/.htpasswd admin    # apache2-utils / httpd-tools
sudo nginx -t && sudo systemctl reload nginx
```

### 6.3 关于鉴权

应用本身**没有任何登录/权限**（红线：不做登录/权限）。所有写接口——`POST /api/demo/reset`、跑 Agent、通过/驳回、删批次、总控对话——默认对能访问的人全部开放，会消耗真实 LLM/生图额度并改写演示数据。公网部署必须至少做到其一：

1. nginx Basic Auth（上面配置）只保护管理端，`/trace/` 与 `/api/trace/` 保持公开；或
2. 安全组/防火墙只放行固定 IP；或
3. 只在内网/现场局域网开，不做公网映射。

**先上 HTTPS 再开 Basic Auth**，否则口令明文传输。完全公开的竞赛演示环境可以删掉两处 `auth_basic`，但要接受任何人可 reset/跑批/删数据，demo 结束后用 `POST /api/demo/reset` 恢复。

### 6.4 HTTPS 与防火墙

```bash
sudo certbot --nginx -d example.com
sudo ufw allow 22,80,443/tcp
```

只开 22/80/443；8000 只监听 `127.0.0.1`，不要对公网放行。切到 HTTPS 后把 `PUBLIC_BASE_URL` 改成 `https://example.com`，并重跑 `POST /api/demo/reset`，让二维码与 H5 链接同步。

## 7. 数据与备份

运行期数据都在 `backend/data/`：

| 路径 | 内容 | 是否必须备份 |
| --- | --- | --- |
| `backend/data/app.db`（含 `-wal`/`-shm`） | SQLite 业务数据 | 是 |
| `backend/data/artifacts/` | 包装 PNG、IP 插画等落盘文件 | 是 |
| `backend/data/image-cache/` | 生图缓存，可重建 | 否 |

SQLite 是 WAL 模式，运行中直接拷 `app.db` 可能不一致；用 `.backup`（需要 sqlite3 命令行，Ubuntu 装 `sqlite3` 包）：

```bash
mkdir -p /var/backups/ruralsmartmark
sqlite3 /opt/ruralsmartmark/backend/data/app.db \
  ".backup '/var/backups/ruralsmartmark/app-$(date +%F).db'"
tar czf "/var/backups/ruralsmartmark/artifacts-$(date +%F).tar.gz" \
  -C /opt/ruralsmartmark/backend/data artifacts
```

恢复：停服务 → 替换 `app.db` → 恢复 `artifacts/` → `chown -R rsm:rsm backend/data` → 起服务 → `curl /api/health`。

生图缓存清理（默认 30 天 / 512MB，支持预演）：

```bash
cd /opt/ruralsmartmark/backend
sudo -H -u rsm .venv/bin/python -m ruralsmartmark.maintenance image-cache --dry-run
```

## 8. 更新发布

```bash
cd /opt/ruralsmartmark
sudo -H -u rsm git pull --ff-only

cd backend
sudo -H -u rsm uv sync --frozen --no-dev
sudo -H -u rsm .venv/bin/alembic upgrade head

cd ../frontend
sudo -H -u rsm pnpm install --frozen-lockfile
sudo -H -u rsm pnpm build

sudo systemctl restart ruralsmartmark
curl -fsS http://127.0.0.1:8000/api/health
```

- 重启会中断正在跑的 Agent 与 SSE 连接；挑没有跑批的时间发布。
- 迁移没有保证可回滚；发布前先做 §7 备份。
- `.env` 不在 git 里，`git pull` 不会覆盖，但新增配置项要对照 `.env.example` 手动补。

## 9. 首次上线验收

1. `curl -fsS http://127.0.0.1:8000/api/health` 返回 `db: ok`。
2. 管理端 `http://example.com/` 弹 Basic Auth，登录后沙盘能加载、3D 能出画面。
3. 未登录直接打开 `http://example.com/trace/ZTDEMO26` 不弹认证，H5 四章内容完整；刷新不 404（SPA 回退生效）。
4. 二维码指向公网地址：`curl -s http://example.com/api/trace/ZTDEMO26/qr.png -o /tmp/qr.png`，用手机扫（或 `zbarimg /tmp/qr.png`）确认 payload 是 `https://example.com/trace/ZTDEMO26`，不是 `127.0.0.1`。
5. 包装 PNG 可访问：`curl -sI http://example.com/api/trace/ZTDEMO26/packaging.png` 为 200。
6. SSE 不断流：管理端打开批次事件，跑一次 mock 流水线；总控发一句话，确认逐字流式、思考过程可展开。nginx 若缓冲会表现为“一次性蹦出来”或 60 秒断线。
7. 重启后数据还在：`systemctl restart ruralsmartmark`，刷新沙盘批次与已审核产出仍在。
8. 手机与服务器不同网络也可扫码（说明公网/域名/HTTPS 生效）；同一 Wi-Fi 的局域网模式仍用 `make lan`，那是 macOS 本机演示入口，不用于服务器。

## 10. 排障

| 现象 | 排查 |
| --- | --- |
| 502 Bad Gateway | `systemctl status ruralsmartmark`；`curl 127.0.0.1:8000/api/health`；看 `journalctl -u ruralsmartmark -n 100` |
| 迁移报 `unable to open database file` | `backend/data` 不存在或属主不是 `rsm`；`mkdir -p` + `chown` |
| 直接打开 `/trace/ZTDEMO26` 404 | nginx 缺 `try_files $uri /index.html` |
| 二维码/包装图指向 `127.0.0.1:5173` | `PUBLIC_BASE_URL` 没改，或 seed 前没设置；改完 `POST /api/demo/reset` |
| 总控/流水线不流式、60s 断 | 反代缺 `proxy_buffering off` / `proxy_read_timeout`；确认 `X-Accel-Buffering: no` 未被中间层吃掉 |
| 登录后 SSE 401 | 浏览器 Basic Auth 凭据未带上；先打开一次管理端页面再触发 SSE；确认 `/api/` 与 `/trace/` 的 location 顺序 |
| 管理端 401 但 H5 正常 | 预期行为：H5 与 `/api/trace/` 公开，其余受保护 |
| 生图/检索超时 | 服务器出网到 SiliconFlow/Firecrawl；有系统代理时设 `FIRECRAWL_TRUST_ENV=true`；`IMAGE_TIMEOUT_SECONDS` 默认 120 |
| 页面静态资源 403 | `dist/` 权限或 nginx 用户读不到 `/opt/ruralsmartmark/frontend/dist` |

## 11. 已知限制

- 单 worker、SQLite 单写：不支持多实例部署与高并发；进程重启会中断进行中的 Agent 任务。
- 无应用层账号体系（红线），鉴权完全依赖 nginx/网络层。
- 溯源 H5 的 `/api/trace/{code}/chat` 公开且会调用 LLM；公网如需控成本，在 nginx 对 `/api/trace/` 加 `limit_req` 或关闭该入口。
- 手机真机扫码、包装厂书面报价、真实盒型/刀版仍未完成；固定演示码不依赖现场 LLM/生图，断网也能打开 H5。
- 不做 Docker；`make dev` / `make lan` 只用于本机开发与局域网演示，不要拿它们当生产进程。

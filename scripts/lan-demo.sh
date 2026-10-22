#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAN_IP="${LAN_IP:-$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)}"

if [ -z "$LAN_IP" ]; then
  echo "没有找到局域网 IP；请确认已连 Wi-Fi，或显式传 LAN_IP=192.168.x.x make lan"
  exit 1
fi

if lsof -ti tcp:8000 >/dev/null 2>&1 || lsof -ti tcp:5173 >/dev/null 2>&1; then
  echo "8000 或 5173 已被占用，请先停掉现有的 make dev / 手动 dev 服务"
  exit 1
fi

BASE_URL="http://$LAN_IP:5173"
echo "局域网地址：$BASE_URL"
echo "固定演示码：$BASE_URL/trace/ZTDEMO26"
echo "手机需与电脑在同一 Wi-Fi；首次可能弹出 macOS 防火墙提示，请允许。"
echo

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  for port in 8000 5173; do
    pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
    [ -n "$pids" ] && kill $pids 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

(
  cd "$ROOT/backend"
  PUBLIC_BASE_URL="$BASE_URL" uv run alembic upgrade head
  PUBLIC_BASE_URL="$BASE_URL" uv run python -m ruralsmartmark.seed
  PUBLIC_BASE_URL="$BASE_URL" uv run ruralsmartmark
) &
BACKEND_PID=$!

(
  cd "$ROOT/frontend"
  pnpm dev --host 0.0.0.0 --strictPort
) &
FRONTEND_PID=$!

for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
if ! curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
  echo "后端在 60 秒内没有就绪，请查看上面的日志。"
  exit 1
fi

curl -fsS -X POST http://127.0.0.1:8000/api/demo/reset >/dev/null
echo "已启动；二维码已指向 ${BASE_URL}。按 Ctrl-C 停止。"
wait

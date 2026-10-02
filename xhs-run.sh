#!/usr/bin/env bash
# 小红书 MCP · 启动器（言棣 2026-10-01 建，跑在 workspace/tools 下，不碰系统）
# 用法：bash xhs-run.sh            —— 起 Xvfb + 服务（前台运行，供长驻会话持有）
#        bash xhs-run.sh status     —— 看服务健康（405 = 活着）
set -u
ROOT=/home/ubuntu/workspace/tools
BIN="$ROOT/bin/xhs-mcp"
export XDG_CACHE_HOME="$ROOT/cache"          # 浏览器内核对到我的目录，别写 ~/.cache
export COOKIES_PATH="$ROOT/cookies.json"     # 铁律：绝不在源码目录里启动
export DISPLAY=:99
PORT=:18061

if [ "${1:-run}" = "status" ]; then
  pgrep -f 'Xvfb :99' >/dev/null && echo "Xvfb: 活" || echo "Xvfb: 死"
  pgrep -f "$BIN" >/dev/null && echo "xhs-mcp: 活" || echo "xhs-mcp: 死"
  curl -s -o /dev/null -w 'HTTP %{http_code}（405=健康）\n' --max-time 5 "http://localhost:18061/mcp" || true
  exit 0
fi

mkdir -p "$XDG_CACHE_HOME"
pgrep -f 'Xvfb :99' >/dev/null || { Xvfb :99 -screen 0 1280x900x24 >"$ROOT/xvfb.log" 2>&1 & sleep 2; }
echo "[$(date '+%F %T')] 启动 xhs-mcp（端口 18061，DISPLAY=:99，COOKIES_PATH=$COOKIES_PATH）"
cd / && exec "$BIN" -headless=false -port "$PORT"

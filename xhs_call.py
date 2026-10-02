#!/usr/bin/env python3
"""小红书 MCP 客户端（言棣 2026-10-01 写）

用法：python3 xhs_call.py <工具名> '<json参数>'
      python3 xhs_call.py list                 # 列出 18 个工具
服务地址默认 http://localhost:18061/mcp，可用 XHS_MCP_URL 覆盖。
"""
import json, os, sys, urllib.request

URL = os.environ.get("XHS_MCP_URL", "http://localhost:18061/mcp")
HEAD = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


def rpc(payload, session=None):
    h = dict(HEAD)
    if session:
        h["Mcp-Session-Id"] = session
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=600) as r:
        sid = r.headers.get("Mcp-Session-Id")
        raw = r.read().decode("utf-8", "ignore")
    if not raw.strip():                       # 通知类请求返回 202 + 空正文
        return {}, sid
    try:
        return json.loads(raw), sid
    except Exception:
        for line in raw.splitlines():          # SSE 兜底
            if line.startswith("data:"):
                return json.loads(line[5:].strip()), sid
        raise


def main():
    init, sid = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                "clientInfo": {"name": "yandi", "version": "1"}}})
    rpc({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    which = (sys.argv[1] if len(sys.argv) > 1 else "list").strip()
    if which == "list":
        res, _ = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, sid)
        for t in res.get("result", {}).get("tools", []):
            print(f"- {t['name']}：{(t.get('description') or '').splitlines()[0][:70]}")
        return
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].strip() else {}
    res, _ = rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                  "params": {"name": which, "arguments": args}}, sid)
    limit = int(os.environ.get("XHS_MAX", "4000"))
    print(json.dumps(res, ensure_ascii=False, indent=2)[:limit])


if __name__ == "__main__":
    main()

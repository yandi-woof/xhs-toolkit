#!/usr/bin/env python3
"""取小红书登录二维码 → 存成 PNG（言棣 2026-10-01）

用法：python3 xhs_qr.py [输出路径]
默认写到 relay 的 uploads 目录，好让小琳在另一块屏幕上打开扫码。
"""
import base64, json, os, sys, urllib.request

URL = os.environ.get("XHS_MCP_URL", "http://localhost:18061/mcp")
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/workspace/data/linqizhidi-runtime/relay/uploads/xhs-qr.png"
HEAD = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


def rpc(payload, session=None):
    h = dict(HEAD)
    if session:
        h["Mcp-Session-Id"] = session
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        sid = r.headers.get("Mcp-Session-Id")
        raw = r.read().decode("utf-8", "ignore")
    if not raw.strip():
        return {}, sid
    try:
        return json.loads(raw), sid
    except Exception:
        for line in raw.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip()), sid
        raise


init, sid = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                 "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                            "clientInfo": {"name": "yandi", "version": "1"}}})
rpc({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
res, _ = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
              "params": {"name": "get_login_qrcode", "arguments": {}}}, sid)
items = res.get("result", {}).get("content", [])
text = ""
png = None
for it in items:
    if it.get("type") == "text":
        text = it.get("text", "")
    elif it.get("type") == "image":
        png = base64.b64decode(it.get("data", ""))
if not png:
    print("没拿到二维码：", json.dumps(res, ensure_ascii=False)[:500])
    sys.exit(1)
open(OUT, "wb").write(png)
print("提示语：", text)
print("已写入：", OUT, os.path.getsize(OUT), "字节")

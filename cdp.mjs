// 直接连小红书 MCP 内置浏览器的调试口（言棣 2026-10-01）
// 用法：node cdp.mjs list
//       node cdp.mjs eval "location.href"
//       node cdp.mjs type "866671"      # 往当前焦点输入框打字并回车
const BASE = process.env.CDP_PORT ? `http://127.0.0.1:${process.env.CDP_PORT}` : "http://127.0.0.1:41319";

async function targets() {
  const r = await fetch(`${BASE}/json/list`);
  return await r.json();
}

function pick(list) {
  const pages = list.filter(t => t.type === "page" && t.webSocketDebuggerUrl);
  return pages.find(t => /xiaohongshu|login/i.test(t.url || "")) || pages[0];
}

function connect(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url);
    ws.onopen = () => resolve(ws);
    ws.onerror = (e) => reject(e);
  });
}

function send(ws, id, method, params = {}) {
  return new Promise((resolve) => {
    const onMsg = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id === id) { ws.removeEventListener("message", onMsg); resolve(m); }
    };
    ws.addEventListener("message", onMsg);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

const [cmd, arg] = process.argv.slice(2);
const list = await targets();
if (cmd === "list") {
  for (const t of list) console.log(t.type, "|", t.title, "|", (t.url || "").slice(0, 120));
  process.exit(0);
}
const t = pick(list);
if (!t) { console.error("没找到页面"); process.exit(1); }
const ws = await connect(t.webSocketDebuggerUrl);
await send(ws, 1, "Runtime.enable");
if (cmd === "eval") {
  const r = await send(ws, 2, "Runtime.evaluate", { expression: arg || "1", returnByValue: true, awaitPromise: true });
  console.log(JSON.stringify(r.result?.result?.value ?? r.result, null, 2).slice(0, 3000));
} else if (cmd === "type") {
  const r = await send(ws, 3, "Input.insertText", { text: arg || "" });
  await new Promise(r2 => setTimeout(r2, 300));
  const r4 = await send(ws, 4, "Input.dispatchKeyEvent", { type: "keyDown", windowsVirtualKeyCode: 13, key: "Enter", code: "Enter" });
  const r5 = await send(ws, 5, "Input.dispatchKeyEvent", { type: "keyUp", windowsVirtualKeyCode: 13, key: "Enter", code: "Enter" });
  console.log("typed", JSON.stringify([r.result, r4.result, r5.result]).slice(0, 300));
} else {
  console.log("用法：node cdp.mjs list|eval|type");
}
ws.close();

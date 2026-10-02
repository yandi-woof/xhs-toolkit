# xhs-toolkit

给 [xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) 配的一副小工具：命令行调它的 18 个工具、把登录二维码存成图片、以及在**验证码必须填在"电脑那一侧"**时替你打字。

我们踩了一晚上才把这条链路走通，这里只留能省时间的部分。

## 文件

| 文件 | 作用 |
| --- | --- |
| `xhs_call.py` | 调任意 MCP 工具：`python3 xhs_call.py list` / `python3 xhs_call.py search_feeds '{"keyword":"..."}'`；用 `XHS_MAX` 控制输出长度（默认 4000 字符，JSON 会被截断导致解析失败时记得调大） |
| `xhs_qr.py` | 取登录二维码并落成 PNG（默认写到你的 web 目录，方便在另一块屏幕上打开扫码） |
| `cdp.mjs` | 直连内置 Chrome 的 DevTools 口：`list` 看页面 / `eval "<js>"` 读 DOM / `type "<文本>"` 往当前焦点输入框打字并回车 |
| `xhs-run.sh` | 启动器：虚拟屏 + 服务（已经带上下面那两条避雷参数） |

依赖：Node 22+（编译/运行 xiaohongshu-mcp）、Python 3（脚本无第三方依赖）、装了 `Xvfb`。

## 四个坑（照抄就省一晚上）

### 1. cookie 路径优先级

`COOKIES_PATH` 环境变量 ＞ 当前工作目录 `cookies.json` ＞ `/tmp/cookies.json`。

如果你在**源码目录里**启动服务，那里往往躺着一个空的 `cookies.json`，会把有效的那份顶掉——症状是"登录状态显示已登录，但评论区全是『登录后评论』"。

**正确姿势**：`cd /` 再启动，并显式指定 `COOKIES_PATH`。

### 2. 二维码每出一张，上一张立刻作废

有效期只有 2-4 分钟。**不要一边生成新码一边让人扫旧码**——我们从 21:29 到 21:43 一共废掉七张，日志里全是「未检测到扫码（超时或已被新的二维码取代）」。

正确做法：先喊人站到位，再生成，扫完立刻查状态。

### 3. 验证码发到手机上，但要填在**电脑那一侧**

扫码成功后，小红书会把短信验证码发到你手机，**可手机 App 里没有输入框**——那个输入框在电脑这张登录页上。

而这张页面跑在服务端的浏览器里：平时你既看不见也点不到。

**解法**：内置 Chrome 带着调试口，本机可以直连。找出端口——

```bash
for p in $(ss -ltn | awk 'NR>1{print $4}' | sed 's/.*://' | sort -n | uniq); do
  curl -s -m 1 "http://127.0.0.1:$p/json/version" | grep -q Chrome && echo "debug port: $p"
done
```

然后：

```bash
node cdp.mjs list                                   # 看有哪些页面
node cdp.mjs eval "document.querySelectorAll('input').length"
node cdp.mjs eval "[...document.querySelectorAll('input')][3].focus()"
node cdp.mjs type "123456"                          # 把码打进那个输入框并回车
```

（注意端口会变：浏览器重启后要重新找。）

### 4. 受限沙箱里 Chrome 起不来

在 bwrap/seccomp/`NoNewPrivileges` 之类的受限环境里，Chrome 会以
`chrome_crashpad_handler: --database is required` 加一个 core dump 收场——**这不是缺库**（`chrome --version` 和 `ldd` 都是好的），是它的沙箱和你的沙箱打架。

**解法**：把服务放到沙箱之外跑（我们最后做成 systemd 服务），别在受限 shell 里硬刚。

## 快速开始

```bash
git clone https://github.com/xpzouying/xiaohongshu-mcp.git && cd xiaohongshu-mcp
npm ci --omit=dev

# 起服务（详见上面第 4 条：要在不受限的环境里跑）
Xvfb :99 -screen 0 1280x900x24 &
cd / && COOKIES_PATH=/path/to/cookies.json DISPLAY=:99 \
  xhs-mcp -headless=false -port :18061

# 取码 → 人扫 → 查状态
python3 xhs_qr.py
python3 xhs_call.py check_login_status
python3 xhs_call.py search_feeds '{"keyword":"关键字"}'
```

## 边界（我们给自己的规矩，仅供参考）

- **只读优先**：搜索、读笔记、读评论、看未读；发帖/评论/点赞这类动作要么不做，要么先给真人过目——**它没有"删除笔记"的工具**。
- **别刷**：一次搜索就翻几十上百条，很容易被风控盯上。一次一屏、慢慢来。
- **cookie 是账号钥匙**：`chmod 600`，不进 git、不进日志。

## License

MIT（仅指本仓库这几个脚本；`xiaohongshu-mcp` 本身有它自己的许可）。

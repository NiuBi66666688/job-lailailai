# 生成后验证

**不要声称「应该能跑」。** 用无头 Chrome 实际渲染并截图确认。

环境事实（Windows 本机实测）：
- Chrome：`/c/Program Files/Google/Chrome/Application/chrome.exe`
- Edge 备用：`/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe`
- 托管 Python：`C:/Users/WQZS6/.workbuddy-ai/binaries/python/versions/3.13.12/python.exe`
- 临时文件写工作区**绝对路径**，不要用 `/tmp`（Git Bash 与 Windows Python 看到的 `/tmp` 不是同一个目录）

## 步骤 1 · 静态自检

```bash
python scripts/render.py --selftest jobs.json
python -c "import re,sys; s=open(sys.argv[1],encoding='utf-8').read(); \
print('size',len(s)); print('script tags', s.count('<script')); \
print('has JOBS', 'JOBS' in s)" output.html
```

确认：文件有内容、`<script>` 标签成对、模板占位未被残留（搜 `{{`、`TODO`）。

## 步骤 2 · JS 运行时错误检查

首屏空白/元素没渲染 **≠ CSS 问题，先查 JS 抛错**。

```bash
cd "<输出目录>" && "C:/Users/WQZS6/.workbuddy-ai/binaries/python/versions/3.13.12/python.exe" -m http.server 8899 --bind 127.0.0.1
```

用 `run_in_background: true` 起服务（不要用 `&`，会端口占用）。然后注入错误钩子：

```bash
python -c "
s=open('output.html',encoding='utf-8').read()
hook='''<script>window.__err=[];window.addEventListener('error',function(e){window.__err.push((e.message||'?')+' @@line'+(e.lineno||'?'));document.title='ERR|'+window.__err.join(' ;; ');});</script>
'''
i=s.rfind('</head>')
open('_probe.html','w',encoding='utf-8').write(s[:i]+hook+s[i:])
"
chrome --headless=new --disable-gpu --dump-dom --virtual-time-budget=6000 \
  "http://127.0.0.1:8899/_probe.html?cb=$(date +%s)" 2>/dev/null | grep -o '<title>[^<]*</title>'
```

- `@@line` 会给出报错行号
- **注入位置必须用 `rfind('</head>')` 或 `rfind('</body>')`**。
  用 `replace(..., 1)` 会命中 JS 字符串里的 `</body>`，把脚本插进字符串中间——
  脚本不执行也不报错，表现为「什么都没发生」，极难排查。
- ⚠️ **钩子的 `<script>` 必须自己闭合**，不要在结尾多写一个 `<script>`。
  悬空的 `<script>` 会一直吞到页面里第一个 `</script>` 为止，把后面的 `<body>`
  整段当成脚本解析，报 `Uncaught SyntaxError: Unexpected token '<'`。
  这个报错**指向的行号是 `</head>` 那一行**，且表现为「页面元素只渲染出第一条」——
  很容易误判成页面本身的 bug。历史上本文件就踩过这个坑（v1.1 修正）。
  判据：报错行号落在 `</head>`/`<body>` 附近、且所有 `.tab`/`.jd-item` 计数恒为 1，
  就是钩子写错，不是页面错。

同时数一下本该由 JS 生成的元素有没有出现：

```bash
... | grep -o 'class="tab ' | wc -l     # 应等于岗位数
... | grep -o 'class="repo' | wc -l
```

## 步骤 3 · 截图验收

```bash
chrome --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1440,4200 \
  --screenshot="<工作区绝对路径>/shot.png" \
  --virtual-time-budget=9000 \
  "http://127.0.0.1:8899/output.html?cb=$(date +%s)"
```

- `--window-size` 高度给大（如 `1440,4200`）可截整页
- 整页图用 Pillow 切段再看，否则被缩放得看不清
- **一定要加 `?cb=$(date +%s)`**，否则 Chrome 缓存旧 DOM

### 关键：`--virtual-time-budget` 不推进 CSS transition
由合成器时钟驱动的 `transition` 不会随虚拟时间推进，进场动画会卡在中间态，
截出来一片半透明。这是**截图假象，不是代码问题**。
验证最终态：探针里加

```html
<style>.rv{opacity:1!important;transform:none!important;transition:none!important}</style>
```

> 本页当前**没有进场动画**（只有 hover / focus / 展开这类交互态过渡），
> 所以直接截图拿到的就是最终态，不需要额外禁用过渡。

## 步骤 4 · 逐项确认清单

| 检查项 | 怎么验 |
| --- | --- |
| 岗位切换器渲染出全部岗位 | 数 `.tab` 数量 == `jobs.length` |
| 切换岗位内容联动 | 用 `--dump-dom` 注入 `switchJob(1)` 后比对 `#jdBox` 文本变化 |
| `[待补充]` 红色高亮 | 搜 `class="placeholder"` 数量 > 0 |
| `【示例写法】` 紫色高亮 | 搜 `class="example"` |
| 第 5 步勾选持久化 | 注入 `localStorage.setItem('..._chk','[1,0,1]')` 后重渲染，确认勾选态 |
| 无 JS 报错 | 步骤 2 的 title 不含 `ERR|` |
| 三个主题都正常 | `--theme art` / `biz` 各生成一次截图 |

## 步骤 5 · 清理

删掉 `_probe.html`、截图 PNG、临时目录。**只留最终交付物。**

## 常见故障速查

| 现象 | 原因 |
| --- | --- |
| 首屏空白 | JS 抛错（步骤 2）；或脚本插入位置错了 |
| 岗位切换无反应 | `switchJob` 未挂到 window（内联 `onclick` 需要全局函数） |
| 截图一片半透明 | CSS 动画未完成，加 `--virtual-time-budget` 并禁用 transition |
| 截图看的是旧内容 | 没加 `?cb=$(date +%s)` |
| 数字/中文乱码 | 输出文件未写 `charset=UTF-8` |
| `--dump-dom` 输出的 HTML 里样式丢失 | 正常，`dump-dom` 不含 computed style，看结构不看样式 |

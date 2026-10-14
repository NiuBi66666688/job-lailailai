# 更新记录

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.1.0] · 2026-10-14

视觉层重做 + 跨平台迁移修复。

### 新增

- **token 驱动的视觉层**：新增 `scripts/design_systems.py`，把颜色/字体/间距/圆角/投影
  全部收敛成 token。`render.py` 只写结构，一律引用 `var(--token)`。
- **三套真实设计系统**：三个学科轨道各绑一套（来自 [OpenDesign](https://github.com/nexu-io/open-design)，
  Apache-2.0）——`sci`→Vercel、`art`→Editorial、`biz`→Stripe。
  三套系统的明度层级、字重习惯、投影逻辑互不相同，不是同一套皮换色。
- **纯 Python oklab 混色**：构建期把上游的 `color-mix(in oklab, …)` 预解析成具体色值，
  摘掉产出物对 Chrome 111+ / Safari 16.2+ 的依赖。
- **派生 token**：`-soft`（角色色 8% 混入主题表面）与 `-ink`（角色色 35% 混向主题文字色），
  解决「角色色直接压在自身浅底上对比度不够」的问题。
- `references/design-systems.md`：token schema、换主题方法、anti-AI-slop 清单。
- `examples/jobs.sample.json`：可运行样例数据（2 个岗位，覆盖 sci / art 双轨）。

### 修复

- **`install.py` 自检在非默认安装位置必然失败**。原实现断言「WorkBuddy 默认路径 == 源码目录」，
  导致包一旦被拷到别处，`--selftest` 就报错——而这恰好卡住「迁移到异地」这个主场景。
  改为判断「目标目录是不是源码自身」。
- **`references/verify-render.md` 探针注入代码的悬空 `<script>`**。原示例结尾多写了一个
  未闭合的 `<script>`，会一直吞到页面里第一个 `</script>`，把整段 `<body>` 当脚本解析，
  报 `Unexpected token '<'`。这个报错指向 `</head>` 那一行，极容易被误判成页面本身的 bug。
  已修正示例并补充判据说明。

### 变更

- **去 AI 味**：移除首屏紫蓝渐变与径向光晕、双品牌色、满屏大圆角、到处都有的卡片投影；
  结构件里的彩色 emoji 改为单色字形（`◎ 图 检 策 § ⓘ`）。页脚祝语的 🚀 有意保留。
- `render.py` 的 `THEMES` 不再包含视觉字段，只管文案（轨道叫什么、第 4 步叫什么），与视觉解耦。
- `SKILL.md` 阶段四重写：加入设计系统对照表与「改样式前先读 design-systems.md」的提示。

### 打包

- 迁移包版本同步到 `1.1.0`，含 21 个文件，附 `MANIFEST.txt`（SHA256）。
- `verify.py` 的必检清单扩到 19 个文件，新增 `design_systems.py` 自检与三主题渲染冒烟测试。

---

## [1.0.0] · 2026-10-12

首个可移植版本。

### 新增

- 五步流水线：岗位定锚 → 定制简历 → 项目成果 → 二创来源 → 蜕变路线。
- 五个零依赖 Python 脚本：`match_score.py` / `split_jd.py` / `render.py` /
  `install.py`，以及配套的 `verify.py`。
- 八份细则文档：检索配方、文理双轨维度库、简历规则、二创矩阵、数据契约、
  渲染验证、跨平台坑位。
- 跨平台安装：WorkBuddy / Claude Code / Qoder CN / Cursor / Codex。
- 单文件 HTML 产出：内联 CSS/JS，零外部请求，双击即开。

[1.1.0]: https://github.com/NiuBi66666688/job-lailailai/releases/tag/v1.1.0
[1.0.0]: https://github.com/NiuBi66666688/job-lailailai/releases/tag/v1.0.0

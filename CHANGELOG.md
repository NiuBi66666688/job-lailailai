# 更新记录

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [2.0.0] · 2026-10-18

**三级能力体系** + **第 6 步能力迁移矩阵**。主版本号跳级是因为产物流水线从五步变六步、
`jobs.json` 增加了必填之外的新段落，且新增了一个确定性算分脚本——虽然老数据仍渲染五步版本。

### 新增

- **`references/capability-tiers.md`（三级能力体系）**。按**行业绑定程度**把能力分三层，
  唯一裁决口径是「看证据的验收方是谁」：`L1` 垂类专属（行业内部的人验收）/
  `L2` 非垂类通用（通用管理标尺验收）/ `L3` 跨类迁移（元能力，无相邻替代品）。
  含 4 问判定树、易混淆情形判定表（7 种典型误判）、16 项能力目录（每项五要素：
  能力定义 / 核心可迁移点 / 垂类适配场景 / 非垂类适配场景 / 跨行业应用案例）、
  五级行为锚点分级标准与职级映射、软能力→硬贡献六槽句式库。
- **`scripts/capability_matrix.py`**。确定性算分：三层加权命中率
  （`W_TIER = L1 0.50 / L2 0.30 / L3 0.20`）、跨层同族能力 `0.6` 迁移折价、
  **最大余额法**保证三层占比三项和恒为 100、A/B/C/D 四场景判定、
  最小补齐路径（按权重降序 + 层级升序 + id 升序稳定排序）。
  11 条自检断言覆盖确定性、边界、单调性、占比守恒、场景可达性、老数据兼容。
- **第 6 步「能力迁移」**。三层占比条 + 场景判定条 + 三层命中卡片
  （熟练度点阵 / 行业跨度 / JD 命中徽标 / 证据原文）+ 缺口清单 + 跳板路径。
  **刻意不在 JS 里做任何算术**——两份实现必然漂移，页面只显示脚本算好的数。
- **`examples/profile.sample.json`**。可运行样例：10 项能力跨三层、1 项软能力走句式库、
  2 处 `[待补充]`、多行业 `scope`，跑出来有真实缺口而不是全绿。
- **能力盘点问答轮**（`SKILL.md` 阶段一第 4 轮，Q11–Q14）+ 答案→字段转换表 + 硬约束
  （每层≥1 项、总数 5–16 项、`lv` 必须有依据、`soft:true` 必须走句式库）。
- **`data-contract.md` 的 `profile.json` 完整契约**。此前 README 指向它但文件里根本没有，
  属于文档缺陷，本次补齐（12 行字段表 + 示例）。
- **三层能力色 token**：`--cap-l1/2/3` 及其 `-soft` / `-ink` 派生，共 10 个新 token
  （总数 76→86）。用**同色相三级明度**而非三个语义色——三层是同一光谱的三段，
  不是三种无关类型。`design_systems.py` 新增自检断言三档明度严格递增。

### 修复

- **`render.py` 用 `abs(hash(title))` 做 localStorage key**。`hash()` 受 `PYTHONHASHSEED`
  影响，同一份数据两次渲染会得到不同 key，导致重渲染后旧的勾选进度全部丢失、
  产出文件无法逐字节比对。改用 `sha1()`。
- **`data-contract.md` 漏记 `jobs[].major` / `jobs[].grade`**。`render.py` 一直在读这两个字段，
  但契约里从未写过——照文档构造的数据会静默丢掉专业与届别。

### 变更

- 产物流水线 **五步 → 六步**，第 6 步挂在第 5 步之后；`switchJob` 与 `renderAll`
  都要调 `renderStep6()`（只挂后者是静默失败：切岗位后缺口清单停在上一个岗位，页面不报错）。
- `render.py` 新增 `--no-cap`；老数据（无 `capabilities`）自动退回五步版本，
  **与 v1.1 逐字节一致**。
- `references/track-dimensions.md` 加了边界声明：本文件只管「怎么练」，不管「属于哪层」，
  层级判定一律查 `capability-tiers.md`。
- `verify.py` 必检清单 19 → 22 个文件，检查项 8 → 12：
  新增「能力目录一致性」（文档 id 集合 == `CATALOG` 键集合）、
  「第 6 步接线检查」（源码层面断言 `renderStep6` 同时挂在 `renderAll` 与 `switchJob`）、
  `capability_matrix.py` 自检、「能力矩阵端到端」（profile+jobs → 矩阵自洽 → 渲染出第 6 步）。
  三主题渲染冒烟增加 3 项断言：第 6 步存在、`--cap-l1/2/3` 齐全、三档明度严格递增；
  另加一条五步兼容路径检查。

### 打包

- 迁移包版本 `2.0.0`，含 24 个文件。
- 配图新增 `flow-tiers.png`（三级能力体系）与 `shot-step6.png`（第 6 步），
  `flow-pipeline.png` 重绘为六步。

---

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

[2.0.0]: https://github.com/NiuBi66666688/job-lailailai/releases/tag/v2.0.0
[1.1.0]: https://github.com/NiuBi66666688/job-lailailai/releases/tag/v1.1.0
[1.0.0]: https://github.com/NiuBi66666688/job-lailailai/releases/tag/v1.0.0

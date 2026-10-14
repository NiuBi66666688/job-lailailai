# job-lailailai · 工作岗位速来-引导

> 把**招聘网站的真实岗位 JD**，翻译成**用户可执行的简历蜕变方案**，最终产出一份单文件可视化 HTML 引导页。

[![Python](https://img.shields.io/badge/Python-%3E%3D3.8-3776AB?logo=python&logoColor=white)](#-环境要求)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen)](#-环境要求)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-WorkBuddy%20%7C%20Claude%20Code%20%7C%20Cursor%20%7C%20Codex%20%7C%20Qoder-8957e5)](#-跨平台安装)

一个**可移植的 agent skill**：指令用 Markdown，能力用零依赖 Python 脚本。
不绑定任何一家 agent 平台——拷过去就能用。

---

## 目录

- [这是什么](#这是什么)
- [效果预览](#效果预览)
- [五步流水线](#五步流水线)
- [逐步详解](#逐步详解)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [调用示例](#调用示例)
- [仓库结构](#仓库结构)
- [常见问题](#常见问题)
- [跨平台安装](#跨平台安装)
- [许可与致谢](#许可与致谢)

---

## 这是什么
先通过岗位需求反哺个人简历，他要什么你给什么。
市面上的「简历优化」工具大多给你一段通用套话。这个 skill 走的是另一条路：

| 通用简历工具 | job-lailailai |
| --- | --- |
| 给你一堆「建议多用动词」的套话 | 抓**真实招聘页的 JD 原文**，逐条建「要求 → 你的证据」映射表 |
| 默认服务理工科 | **文理双轨**：人文社科的岗位同样走招聘站检索，作品集/调研报告/策划案都算有效证据 |
| 靠模型感觉打分 | 岗位匹配打分交给**确定性脚本**，同一输入必须同一分数 |
| 输出一段文本 | 输出**单文件 HTML 引导页**，双击即开，零外部请求 |
| 一套皮肤走天下 | 理工/文科/商科各绑一套**真实设计系统**，切换轨道视觉语言真的会变 |

核心承诺：**把用户已有的经历，重写并组织成最贴合目标岗位的表达，总之你懂的**。

---

## 效果预览

完整渲染结果（三套设计系统，同一份数据）：

<table>
<tr>
<td width="33%" align="center"><b>sci · 理工科</b><br><sub>Vercel</sub></td>
<td width="33%" align="center"><b>art · 人文社科</b><br><sub>Editorial</sub></td>
<td width="33%" align="center"><b>biz · 经管商科</b><br><sub>Stripe</sub></td>
</tr>
<tr>
<td><img src="docs/images/hero-sci.png" alt="sci 主题首屏"></td>
<td><img src="docs/images/hero-art.png" alt="art 主题首屏"></td>
<td><img src="docs/images/hero-biz.png" alt="biz 主题首屏"></td>
</tr>
</table>

整页总览（sci 主题）：

<img src="docs/images/full-sci.png" alt="整页总览" width="620">

> 想直接在浏览器里点开看？把 `examples/demo.html` 下载下来双击即可。
> 三套主题的在线预览在 [`docs/preview/`](docs/preview/)。

---

## 五步流水线

<img src="docs/images/flow-pipeline.png" alt="五步流水线">

最终交付一个**单文件 HTML 引导页**：顶部有岗位切换器，切换岗位时第 1–4 步的内容联动更新。

---


## 逐步详解


### 岗位切换器 · 一岗一版

<img src="docs/images/shot-switcher.png" alt="岗位切换器">

切换岗位后，第 1–4 步整体更新。**一岗一版才有意义**，不要混着看。

### 第 1 步 · 岗位定锚

<img src="docs/images/shot-step1.png" alt="第 1 步 岗位定锚">

抓取招聘页正文，抽出 JD 原文与职位要求（**未作改写**），并标注来源、抓取时间、关键词。

### 第 2 步 · 定制简历

<img src="docs/images/shot-step2.png" alt="第 2 步 定制简历">

技能矩阵**按 JD 关键词命中优先级重排**——HR 初筛只看前 1/3 屏，命中词必须靠前。
下方是「要求 → 你的证据」映射表；写不出证据的条目直接进缺口清单。

页面上两种高亮约定：

- <span style="color:#d33">`[待补充：…]`</span> —— 你必须自己回填的真实信息
- <span style="color:#8250df">`【示例写法】`</span> —— 只是表达范式，**请勿照抄内容**

### 第 3 步 · 项目成果

<img src="docs/images/shot-step3.png" alt="第 3 步 项目成果">

P0 必做（简历核心证据）/ P1 加分 / P2 差异化。每个项目必须写明**验收标准**，否则无法证明完成。

### 第 5 步 · 蜕变路线

<img src="docs/images/shot-step5.png" alt="第 5 步 蜕变路线">

90 天时间轴 + 自检清单 + 投递策略。勾选状态通过 `localStorage` 持久化，刷新不丢。

---

## 快速开始

### 环境要求

| 项 | 要求 |
| --- | --- |
| Python | **>= 3.8**（推荐 3.10+）。命令可能是 `python` / `python3` / `py` |
| 第三方依赖 | **无**。五个脚本全部只用标准库，**不需要也不需要执行 `pip install`** |
| 其他运行时 | 不需要 Node、不需要浏览器。只有做「真实渲染验收」时才需要无头 Chrome（可选） |

> 零依赖是刻意的设计——跨平台迁移最大的坑就是依赖装不上。

### 第 1 步 · 获取

```bash
# 方式 A：git clone
git clone https://github.com/NiuBi66666688/job-lailailai.git
cd job-lailailai

# 方式 B：直接下载 Release 里的迁移包 zip，解压到任意目录
```

### 第 2 步 · 验收

```bash
python verify.py
```

全绿即代表这份包在你机器上完好可用（会跑完五个脚本的自检 + **三主题**真实渲染冒烟测试）。
**这一步很关键**：能提前发现 Python 版本、编码、路径等问题，而不是等到真跑业务时才炸。

### 第 3 步 · 落位到 agent 平台

```bash
# 自动探测本机装了哪些平台（只读，不写文件）
python scripts/install.py --detect

# 装到全部探测到的平台（软链模式：改源目录即全平台生效）
python scripts/install.py --target all --link

# 只装某一个平台
python scripts/install.py --target claude-code

# Cursor / Codex 需要 AGENTS.md 指针
python scripts/install.py --target codex --agents-md

# 装到自定义路径（项目级安装 / 未知平台）
python scripts/install.py --target all --dest /path/to/skills
```

装完后在对话里说一句「帮我做求职简历蜕变引导」即可触发。

---

## 配置说明

### `profile.json` · 你的能力底牌

用于岗位匹配打分。字段定义见 [`references/data-contract.md`](references/data-contract.md)。

```json
{
  "major": "计算机科学与技术",
  "degree": "本科",
  "gradYear": 2028,
  "track": "sci",
  "skills": ["Python", "RAG", "向量检索", "Prompt Engineering", "LangChain"],
  "projects": [
    {"name": "企业知识库 RAG 问答 Agent", "stack": ["Python", "LangChain", "Faiss"]}
  ],
  "cities": ["上海", "杭州"],
  "keywords": ["Agent", "大模型", "算法实习生"]
}
```

### `jobs.json` · 岗位数据

每个岗位一条，含 `jd` / `req` / `keywords` / `resume` / `build` / `repos` 六段。
可直接跑 [`examples/jobs.sample.json`](examples/jobs.sample.json) 试链路。

### `render.py` 可选参数

| 参数 | 作用 |
| --- | --- |
| `--theme sci\|art\|biz` | 指定设计系统与文案语气（默认按 jobs 里的 `track` 自动判定） |
| `--title` / `--subtitle` | 覆盖页面标题与副标题 |
| `--no-repo` | 跳过第 4 步（当二创来源确实检索不到时） |

---

## 调用示例

### 命令行 · 确定性工具

```bash
# 1) 岗位匹配打分 —— 确定性、可复现、不烧 token
python scripts/match_score.py --profile profile.json --jobs jobs.json

# 2) 招聘页正文 → 结构化 JD
python scripts/split_jd.py --raw page.txt --out jd.json

# 3) 生成单文件 HTML 引导页
python scripts/render.py jobs.json out.html --title "我的求职蜕变方案"

# 4) 数据完整性自检
python scripts/render.py --selftest jobs.json

# 5) 视觉 token 自检（齐全性 + oklab 混色算法）
python scripts/design_systems.py
```

**为什么打分必须用脚本而不是让模型判断**：

| 环节 | 交给谁 | 原因 |
| --- | --- | --- |
| 岗位匹配打分、关键词命中 | **`match_score.py`** | 同一输入必须同一分数。模型会漂移（今天 73 明天 68），用户立刻失去信任 |
| JD 切分 | **`split_jd.py`** | 段落识别是规则问题，模型容易过度发挥 |
| 简历改写、二创引导、面试建议 | **大模型** | 这才是真正需要判断力的地方 |

### 对话中 · 交给 agent

装好之后直接说人话即可：

```
帮我做求职简历蜕变引导
```

agent 会按 `SKILL.md` 的流程走：先分轮采集（专业 / 届别 / 技能 / 目标，一轮最多 4 题），
再联网检索真实岗位，再调脚本打分切分，最后渲染 HTML 并截图验证。

也可以更具体：

```
我是 2028 届人文社科本科生，想投新媒体运营和品牌公关。
帮我从招聘网站找 3 个真实岗位，做一份定制简历方案。
```

---

## 仓库结构

```
job-lailailai/
├── SKILL.md                    ← 完整工作流（唯一真源，agent 的入口）
├── AGENTS.md                   ← 给只认 AGENTS.md 的平台做指针（Cursor / Codex）
├── README.md                   ← 本文件：使用说明
├── LICENSE                     ← Apache-2.0
├── NOTICE                      ← 上游 OpenDesign 设计系统的署名
├── CHANGELOG.md                ← 版本记录
├── requirements.txt            ← 依赖声明（零第三方依赖）
├── verify.py                   ← 一键验收（clone 后先跑这个）
│
├── scripts/                    ← 零依赖 Python 工具
│   ├── match_score.py            岗位匹配打分（确定性、可复现）
│   ├── split_jd.py               招聘页正文 → 结构化 JD
│   ├── design_systems.py         视觉层 token（Vercel / Editorial / Stripe）
│   ├── render.py                 生成单文件 HTML 引导页
│   └── install.py                跨平台安装（--detect / --target）
│
├── references/                 ← 按需读的细则
│   ├── search-recipes.md         联网检索配方：引擎分工 + 招聘站 site: 定向
│   ├── track-dimensions.md       文理科能力维度库
│   ├── resume-rules.md           定制简历生成规则
│   ├── rework-matrix.md          P0/P1/P2 项目与二创来源矩阵
│   ├── data-contract.md          jobs.json / profile.json 数据契约
│   ├── design-systems.md         视觉层：token schema / 换主题 / anti-AI-slop 清单
│   ├── verify-render.md          渲染验证方法（含无头 Chrome 实操）
│   └── portability.md            跨平台兼容矩阵与坑位
│
├── examples/
│   ├── jobs.sample.json        ← 可运行样例数据（2 个岗位，覆盖 sci/art 双轨）
│   └── demo.html               ← 样例渲染出的单文件页面（sci 主题）
│
└── docs/
    ├── PUBLISH.md              ← 发布上线指南（含每步骤配图要求）
    ├── index.html              ← 预览落地页（GitHub Pages 入口）
    ├── preview/                ← 三主题在线预览页
    │   ├── demo-sci.html
    │   ├── demo-art.html
    │   └── demo-biz.html
    └── images/                 ← README 与 PUBLISH 的配图
```

---

## 常见问题

<details>
<summary><b>平台没自动触发这个 skill？</b></summary>

先 `python scripts/install.py --detect` 确认它落到了被扫描的目录；
也可以在对话里显式 @ 引用，或直接说「按 job-lailailai 的流程做」。
</details>

<details>
<summary><b>Cursor / Codex / 自研 agent 认不出？</b></summary>

它们优先读 `AGENTS.md`。本仓库根目录**已内置** `AGENTS.md`（内容是指针 + 核心要点摘要），
直接用即可；也可以跑 `python scripts/install.py --target codex --agents-md` 生成。
</details>

<details>
<summary><b>Windows 建软链报错？</b></summary>

未开启开发者模式。改用复制模式——去掉 `--link` 参数即可。
</details>

<details>
<summary><b>中文乱码？</b></summary>

Windows 控制台默认 GBK。脚本已强制 UTF-8 输出；若仍乱码先执行 `chcp 65001`。
</details>

<details>
<summary><b>脚本报「找不到文件」？</b></summary>

用了相对路径但 cwd 不对。用绝对路径调用，或先 `cd` 到仓库根目录。
`scripts/` 与 `references/` 的相对路径是写死的，**不要把文件拆散**。
</details>

<details>
<summary><b><code>python</code> 命令不存在？</b></summary>

环境只装了 `python3` 或 `py`。换成 `python3 verify.py` / `py verify.py`。
</details>

<details>
<summary><b>改了颜色但页面没变 / 某个角标还是旧色？</b></summary>

你大概在 `render.py` 里手写了 hex。**颜色只该定义在 `scripts/design_systems.py`**，
`render.py` 里一律 `var(--token)`。手改会让三个主题各自漂移，且下次渲染被覆盖。
要新颜色先在 token 层派生，细则见 [`references/design-systems.md`](references/design-systems.md)。
</details>

<details>
<summary><b>我想让页面更「漂亮」一点，加点渐变和圆角？</b></summary>

先读 [`references/design-systems.md`](references/design-systems.md) 第四节的「有意不做的事」。
首屏渐变光晕、双品牌色、满屏大圆角、到处投影都是被**主动去掉**的 AI 味。
「更漂亮」在本项目里的含义是**更克制**，不是加装饰。
</details>

<details>
<summary><b>怎么确认渲染真的没问题，而不是「应该能跑」？</b></summary>

按 [`references/verify-render.md`](references/verify-render.md) 用无头 Chrome 截图肉眼确认。
`--virtual-time-budget` 不推进 CSS transition，截图半透明是假象，不是代码问题。
</details>

<details>
<summary><b>岗位数据是真的吗？</b></summary>

来自联网检索，每个岗位记录 `url` / `source` / `fetchedAt`。
查不到的会写「未检索到，需人工确认」，**不会把没找到的岗位写成找到了**。
`examples/jobs.sample.json` 是**演示假数据**，只用于验证渲染链路。
</details>

---

## 跨平台安装

本 skill 是**通用格式**，不绑定任何平台：指令用 Markdown、能力用零依赖 Python 脚本，
这两样在所有主流 agent 上都能跑。差异只在入口文件名。

| 平台 | 入口 | 默认位置 |
| --- | --- | --- |
| WorkBuddy | `SKILL.md` | `~/.workbuddy-ai/skills/<name>/` |
| Claude Code | `SKILL.md` | `~/.claude/skills/<name>/` |
| Qoder CN | `SKILL.md` | `~/.qoder/skills/<name>/` |
| Cursor | `AGENTS.md` | 项目根 `/.cursor/rules/` |
| Codex | `AGENTS.md` | 项目根 / `~/.codex/` |

**换平台不影响行为**，因为重活都交给了脚本：打分、JD 切分是确定性代码，
agent 只负责理解意图与改写表达。更多坑位见 [`references/portability.md`](references/portability.md)。

---

## 发布上线

想知道这个仓库是怎么从本地源码推到 GitHub 的、每一步需要什么账号与前置条件、
每个步骤该配什么图？见 **[`docs/PUBLISH.md`](docs/PUBLISH.md)**。

---

## 许可与致谢

- 本项目代码：**Apache-2.0**，见 [`LICENSE`](LICENSE)。
- 三套设计系统 token 取自 [nexu-io/open-design](https://github.com/nexu-io/open-design)
  的 `design-systems/{vercel,editorial,stripe}/`，许可 **Apache-2.0**，
  完整署名见 [`NOTICE`](NOTICE)。本地适配与上游的差异记录在
  `scripts/design_systems.py` 文件头与 [`references/design-systems.md`](references/design-systems.md)。
- Vercel / Editorial / Stripe 是各自权利人的商标，此处仅用于指代设计语言来源。

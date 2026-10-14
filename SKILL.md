---
name: job-lailailai
description: 求职简历蜕变引导。以问答方式收集用户专业/届别/技能/目标，联网检索招聘网站获取真实岗位 JD，为理工科与人文社科双轨定制差异化简历、项目成果清单、二创来源矩阵与执行路线图，最终产出一份可视化五步引导页（可切换岗位联动；理工/文科/商科各自绑定一套真实设计系统，非套壳换色）与配套投递材料。当用户要求「做求职简历蜕变引导」「根据招聘网站生成定制简历」「帮我按岗位改简历」「找工作/实习/校招岗位分析」「文科/理科的岗位能力提升」时使用。
agent_created: true
---

# 求职简历蜕变引导

把「招聘网站的真实岗位」翻译成「用户可执行的简历蜕变方案」。

核心承诺：**把用户已有的经历，重写并组织成最贴合目标岗位的表达**。

## 何时使用

- 用户想根据**真实招聘网站**（校招/社招/实习）的岗位要求，得到一份定制简历
- 用户想要「简历蜕变」「求职规划」「岗位匹配分析」「能力提升计划」
- 用户提到具体公司/岗位，希望知道自己差什么、该做什么项目
- 用户是**人文社科/经管**背景，担心「求职工具只服务理工科」——本 skill 双轨覆盖

## 五步产物流水线

```
① 岗位定锚  →  ② 定制简历  →  ③ 项目成果  →  ④ 二创来源  →  ⑤ 蜕变路线
   JD 原文       关键词对齐       P0/P1/P2      开源/作品集      90天路线图
   与要求        的证据映射      可落地清单     可改造成自己的    +自检+投递策略
```

最终交付一个**单文件 HTML 引导页**：顶部岗位切换器，切换岗位时第 1–4 步内容联动更新。

## 工作流

### 阶段一：问答采集（**必须做，不可跳过**）

用 `AskUserQuestion` 分轮收集。**一轮最多问 4 题**，先问最关键的，后续按需追问。
不要一次抛出十几个问题淹没用户。

**第 1 轮 · 定位**
1. 目标类型：校招 / 实习 / 社招 / 转行
2. 届别与学历：如「大三 · 2028届本科」「研二 · 2029届硕士」
3. 专业与学科轨道：理工科 / 人文社科 / 经管商科（决定后续维度库，见 `references/track-dimensions.md`）
4. 目标城市与公司偏好（可多选，含「不限」）

**第 2 轮 · 能力底牌**
5. 现有技能标签（自由输入，越具体越好：工具、语言、方法论、证书）
6. 现有项目/作品数量与形态（代码仓库 / 作品集 / 调研报告 / 策划案 / 论文 / 竞赛）
7. 期望岗位关键词（可留空，由 skill 联网推荐）

**第 3 轮 · 产出偏好**
8. 目标岗位数量：先锁定 3–5 个（**不要贪多**，一岗一版才有意义），后续再扩
9. 是否需要配套 Word 文档（每个岗位：JD 页 + 定制简历页 + 项目页 + 二创页）
10. 个人信息处理：用占位符 + 填写指引（**默认推荐，保护隐私**）／ 用户直接提供真实信息

若用户已在本轮对话中提供过某项信息，**不要重复问**，直接复用。

### 阶段二：联网检索真实岗位

先读 `references/search-recipes.md`，按其中的引擎分工与查询模板执行。
关键原则：

1. **语言分流**：中文查询走国内引擎（百度 / Bing CN / 360 / 搜狗 / 微信搜一搜 / 神马）；
   英文查询走国际引擎（Google / DuckDuckGo / Brave 等）。
2. **招聘站定向**：用 `site:` 定向主流招聘平台，比泛搜精准得多。
   - 综合：`site:zhipin.com`（BOSS直聘）`site:zhaopin.com`（智联）`site:51job.com`（前程无忧）
   - 校招实习：`site:jobs.bytedance.com` `site:join.qq.com` `site:careers.tencent.com`
     `site:talent.alibaba.com` `site:campus.alibaba.com` `site:hr.baidu.com` `site:job.meituan.com`
     `site:jobs.bilibili.com` `site:campus.163.com` `site:join.huawei.com`
   - 国企/事业单位：`site:zhaopin.com` 国企频道、`site:gongkao.com`、各地人才网
   - 高校就业网：`site:*.edu.cn 就业 招聘 2028届`
3. **文科岗位同样要走招聘站**（运营/市场/品牌/公关/HR/行政/法务/编辑/翻译/教师/公务员），
   不要因为「看起来没有技术 JD」就跳过联网检索。
4. **时效过滤**：加 `tbs=qdr:m`（近一月）或 `qdr:w`（近一周），校招信息时效性强。
5. **正文抓取**：检索到岗位详情页后，抓取正文提取 JD 与职位要求**原文**，不要凭标题臆测。
   若站点禁止跨域/反爬，改用平台公开的岗位摘要，并如实标注来源与抓取时间。
6. **如实标注**：每个岗位记录 `url`、`source`、`fetchedAt`；查不到的写「未检索到，需人工确认」，
   不要把没找到的岗位写成找到了（岗位数据要真实可溯源，否则后面的匹配分析没有意义）。

### 阶段三：结构化

把检索结果整理成 `jobs.json`（schema 见 `references/data-contract.md`）。每个岗位一条，
包含 `jd`/`req`/`keywords`/`resume`/`build`/`repos` 五段。

**定制简历的生成规则**（详见 `references/resume-rules.md`）：
- 技能矩阵**按 JD 关键词命中优先级重排**——HR 初筛只看前 1/3 屏，命中词必须靠前
- 经历按与岗位的相关度重排
- 逐条 JD 要求建立「要求 → 你的证据」映射表；写不出证据的条目进缺口清单
- 每条经历尽量给出量化结果；用户没给数字就写 `[待补充：量化结果，如 X%→Y%]`

**项目推荐**（`references/rework-matrix.md`）：
- P0 必做（简历核心证据）/ P1 加分 / P2 差异化
- **文科学科不许默认推代码项目**——作品集、调研报告、策划案、翻译出版、教案设计、
  数据分析报告同样是有效证据
- 每个项目必须写明「验收标准」，否则无法证明完成

**二创来源矩阵**：不只 GitHub。按学科轨道分流：
- 理工科：GitHub / Gitee / HuggingFace / arXiv 复现
- 人文社科：公众号优秀案例 / 政府公开数据集 / 学术论文 / 公开策划案 / 开源语料
- 经管商科：上市公司年报 / 行业研报 / 商业案例库 / Kaggle 数据集

合规提示必须写进产出：遵守原仓 License、注明 fork 来源与增量。

### 阶段三之二：调用工具做确定性校验（**不要凭感觉打分**）

本 skill 自带确定性工具。**凡是能用工具算的，不要让模型估。**

```bash
# 1) 岗位匹配打分 —— 确定性，可复现，不烧 token
python scripts/match_score.py --profile profile.json --jobs jobs.json

# 2) 招聘页正文 → 结构化 JD
python scripts/split_jd.py --raw page.txt --out jd.json
```

**为什么必须用工具而不是让模型判断**：

| 环节 | 交给谁 | 原因 |
| --- | --- | --- |
| 岗位匹配打分、关键词命中 | **`match_score.py`** | 同一输入必须同一分数。模型会漂移（今天 73 明天 68），用户立刻失去信任 |
| JD 切分 | **`split_jd.py`** | 段落识别是规则问题，模型容易过度发挥 |
| 简历改写、二创引导、面试建议 | **大模型** | 这才是真正需要判断力的地方 |

### 阶段四：生成 HTML

```bash
python scripts/render.py <jobs.json> <输出.html> --title "标题" --subtitle "副标题"
```

`render.py` 会产出单文件页面（内联 CSS/JS，零外部请求，双击即开）。
可选参数：
- `--theme sci|art|biz` 切换设计系统与文案语气（默认按 jobs 中的 track 自动判定）
- `--no-repo` 跳过第 4 步（当二创来源确实检索不到时）

**视觉层由 token 驱动，不要手改色值。** 三个轨道各绑一套真实设计系统：

| 轨道 | 设计系统 | 气质 |
| --- | --- | --- |
| `sci` 理工科 | Vercel | 近白画布 / 近黑文字 / 单一蓝强调 |
| `art` 人文社科 | Editorial | 暖纸面 / 衬线标题 / 赭石强调 |
| `biz` 经管商科 | Stripe | 白底 / 藏青文字 / 紫罗兰强调 |

产出物里所有颜色都写成 `var(--token)`，定义在 `scripts/design_systems.py`。
换主题 = 改一处映射；细则与来源许可见 `references/design-systems.md`。

**改样式前先读 `references/design-systems.md` 的「有意不做的事」一节**——
首屏渐变光晕、双品牌色、满屏大圆角、到处都有的卡片投影、结构件里的彩色 emoji
都是被主动去掉的 AI 味，不要加回来。

生成后**必须验证**（见下），不要声称「应该能跑」。

### 阶段五：验证与交付

1. **结构自检**：`python scripts/render.py --selftest <jobs.json>` 校验数据完整性
2. **真实渲染验收**：按 `references/verify-render.md` 用无头 Chrome 截图，肉眼确认
   - 岗位切换器可切换且内容联动
   - 第 5 步勾选状态能持久化（localStorage）
3. 交付 HTML；若用户要 Word，再据此产出 `.docx`
4. 明确告诉用户：哪些数据来自联网检索（附来源与时间）、哪些是占位符待回填

## 写作原则

要在系统提示与 HTML 的醒目位置同时声明：

| 建议 | 说明 |
| --- | --- |
| 优先用用户提供的真实信息 | 有就给，没有就留 `[待补充：...]` 让用户回填 |
| 把用户已有经历映射到 JD 要求 | 重排顺序、调整表达、改详略 |
| 用 `[待补充：...]` 标出缺口 | 方便用户一眼看到还需要补什么 |

## 跨平台（WorkBuddy / Claude Code / Cursor / Codex / Qoder）

本 skill 是**通用格式**，不绑定任何平台：指令用 Markdown、能力用零依赖 Python 脚本，
这两样在所有主流 agent 上都能跑。差异只在入口文件名，详见 `references/portability.md`。

```bash
# 先探测本机装了哪些平台（只读，不写文件）
python scripts/install.py --detect

# 装到全部探测到的平台（软链模式：改源目录即全平台生效）
python scripts/install.py --target all --link

# 单平台 / Cursor、Codex 需要 AGENTS.md 指针
python scripts/install.py --target claude-code
python scripts/install.py --target codex --agents-md
```

| 平台 | 入口 | 默认位置 |
| --- | --- | --- |
| WorkBuddy | `SKILL.md` | `~/.workbuddy-ai/skills/<name>/` |
| Claude Code | `SKILL.md` | `~/.claude/skills/<name>/` |
| Qoder CN | `SKILL.md` | `~/.qoder/skills/<name>/` |
| Cursor | `AGENTS.md` | 项目根 `/.cursor/rules/` |
| Codex | `AGENTS.md` | 项目根 / `~/.codex/` |

**换平台不影响行为**，因为重活都交给了脚本：打分、JD 切分是确定性代码，
agent 只负责理解意图与改写表达。

## 资源索引

| 文件 | 何时读 |
| --- | --- |
| `references/search-recipes.md` | 阶段二，开始联网检索前 |
| `references/track-dimensions.md` | 阶段一，判定学科轨道后；文理科能力维度库 |
| `references/resume-rules.md` | 阶段三，生成定制简历前 |
| `references/rework-matrix.md` | 阶段三，推荐项目与二创来源时 |
| `references/data-contract.md` | 阶段三，构造 jobs.json 时；含完整字段定义与示例 |
| `references/design-systems.md` | 阶段四，改视觉前；token schema、换主题方法、anti-AI-slop 清单 |
| `references/verify-render.md` | 阶段五，验证 HTML 时 |
| `references/portability.md` | 需要装到别的 agent 平台时；跨平台兼容矩阵与坑位 |
| `scripts/render.py` | 阶段四，生成 HTML |
| `scripts/design_systems.py` | 阶段四，视觉层 token（**改配色/字体/间距只改这里**） |
| `scripts/match_score.py` | 阶段三，岗位匹配打分（**确定性，别让模型估**） |
| `scripts/split_jd.py` | 阶段三之二，招聘页正文 → 结构化 JD |
| `scripts/install.py` | 跨平台安装：`--detect` 探测 / `--target` 安装 |

## 工具速查

| 命令 | 作用 | 自检 |
| --- | --- | --- |
| `match_score.py --profile p.json --jobs j.json` | 批量打分并排序 | `--selftest` |
| `match_score.py --profile p.json --job one.json` | 单岗位打分 | — |
| `split_jd.py --raw page.txt` | 招聘页正文 → JD/要求 | `--selftest` |
| `split_jd.py --raw page.txt --out jd.json` | 同上，写入文件 | — |
| `render.py jobs.json out.html` | 生成引导页 | `--selftest` |
| `design_systems.py` | 视觉 token 自检（齐全性 + 混色算法） | 直接运行 |
| `install.py --detect` | 探测本机 agent 平台 | `--selftest` |
| `install.py --target all --link` | 安装到全部平台 | — |

## 常见错误

- **跳过问答直接生成** → 拿到的是通用模板，不是定制方案。必须先采集。
- **岗位数量贪多** → 7 个以上岗位每版简历都会变浅。先 3–5 个。
- **只搜 GitHub** → 文科用户得不到任何可用产出。必须按轨道分流来源。
- **在 `render.py` 里手改色值** → 颜色只该定义在 `design_systems.py`。手改会让
  三个主题各自漂移，且下次渲染被覆盖。要新颜色就先在 token 层派生。
- **把「更漂亮」理解成加装饰** → 渐变光晕、双强调色、满屏大圆角、到处投影
  都是被主动去掉的 AI 味（见 `references/design-systems.md` 第四节）。
- **声称已验证但没截图** → 本环境 Chrome headless 可用，务必实际渲染确认。

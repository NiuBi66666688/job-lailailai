---
name: job-lailailai
description: 求职简历蜕变引导（三级能力体系）。以问答方式收集用户专业/届别/技能/目标与能力自评，联网检索招聘网站获取真实岗位 JD，把能力拆成「垂类专属 L1 + 非垂类通用 L2 + 跨类迁移 L3」三层，为理工科与人文社科双轨定制差异化简历、项目成果清单、二创来源矩阵、执行路线图与能力迁移矩阵，最终产出一份可视化六步引导页（可切换岗位联动；理工/文科/商科各自绑定一套真实设计系统，非套壳换色）与配套投递材料。支持垂类精准求职、非垂类宽泛择业、跨行业转型求职三种场景。当用户要求「做求职简历蜕变引导」「根据招聘网站生成定制简历」「帮我按岗位改简历」「找工作/实习/校招岗位分析」「文科/理科的岗位能力提升」「跨行业转行怎么做」「我的能力能迁到什么岗位」时使用。
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
- 用户想**转行**、或不确定自己的经历能迁到哪些岗位——第 6 步会算出迁移率与跳板路径

三种择业场景都能跑，由 `profile.intent` 决定判定口径：

| 场景 | `intent` | 判定重点 |
| --- | --- | --- |
| A 垂类精准求职 | `vertical` | `L1` 命中率是否够深——同行看的是你的垂类厚度 |
| B 非垂类宽泛择业 | `broad` | `L2` 命中率是否够广——多行业通用的才是可迁移资产 |
| C 跨行业转型 | `switch` | `L1` 低而 `L2` 高即判转型，靠同族能力折价 0.6 找跳板 |
| D 证据不足 | 自动 | 三层都没达标，先补地基再谈定位 |

## 六步产物流水线

```
① 岗位定锚  →  ② 定制简历  →  ③ 项目成果  →  ④ 二创来源  →  ⑤ 蜕变路线  →  ⑥ 能力迁移
   JD 原文       关键词对齐       P0/P1/P2      开源/作品集      90天路线图      L1/L2/L3 占比
   与要求        的证据映射      可落地清单     可改造成自己的    +自检+投递策略   命中率/缺口/路径
```

最终交付一个**单文件 HTML 引导页**：顶部岗位切换器，切换岗位时第 1–4、6 步内容联动更新。

## 三级能力体系（本 skill 的判断骨架）

能力按**行业绑定程度**分三层，不是按熟练度分。**唯一裁决口径是「看证据的验收方是谁」**：

| 层 | 名称 | 验收方 | 例子 |
| --- | --- | --- | --- |
| `L1` | 垂类专属 | 行业内的人（技术面试官、主编、合规负责人） | 技术方案落地、数据建模与指标口径、内容生产 |
| `L2` | 非垂类通用 | 通用管理标尺（任何行业的 leader 都能判断好坏） | 结构化问题拆解、项目推进、书面表达 |
| `L3` | 跨类迁移 | 求职者自己（元能力，无相邻替代品） | 能力矩阵自评、岗位能力拆解、经历迁移改写 |

三条硬规则，违反任一条结论就是错的：

1. **熟练度高不等于层级高**。十年资深文案的内容能力仍是 `L1`——它的验收方还是主编，不是通用标尺。
2. **`L3` 不打折**。元能力没有相邻替代品，永远不适用迁移折价（`TRANSFER_FACTOR = 0.6`）。
3. **`L2` 必须翻译成硬贡献**。写「沟通能力强」是废话，要走句式库：
   `在【场景/规模】中，用【方法】把【软能力】落到【可交付物】，使【指标】从【A】到【B】。`

完整判定树、16 项目录（含每项的五要素：能力定义 / 核心可迁移点 / 垂类适配场景 / 非垂类适配场景 / 跨行业应用案例）、
分级标准与句式库见 `references/capability-tiers.md`。**写进 jobs.json 的 `capabilities` 前必读**。

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

**第 4 轮 · 能力盘点**（决定第 6 步能否成立，**不要跳过**）

11. 盘点方式：自动推断（从第 2 轮技能标签 + 项目推）／ 自选 16 项清单 ／ 贴简历让我解析
12. 三层归属确认：把推断出的 L1/L2/L3 三组**列给用户改判**（用户最清楚谁在验收自己的证据）
13. 熟练度校准：对 3–5 项关键能力标 `lv`（0 没做过 / 1 跟着做过 / 2 独立做过 / 3 主导过 / 4 教过别人）
14. 迁移意向：只投本行业 ／ 本行业为主但接受相邻 ／ 明确要跨行业（**必问目标行业**）

**答案 → 字段转换**（写进 `profile.json`，schema 见 `references/data-contract.md`）：

| 题号 | 字段 | 转换规则 |
| --- | --- | --- |
| Q11 | `capabilities[].id` `name` `cat` | 只能从 16 项目录取值；确实无法归类才用 `X-<slug>`，且 `tier` 必填 |
| Q12 | `capabilities[].tier` | 覆盖自动推断值。**用户改判优先于模型推断**——验收方只有用户看得见 |
| Q13 | `capabilities[].lv` | 未标级的默认 `2`，且 `evidence` 写 `[待补充：...]`，不许替用户编经历 |
| Q14 | `intent` / `targetIndustry` | `vertical` 只投本行业 ／ `broad` 宽泛择业 ／ `switch` 跨行业（配 `targetIndustry`） |
| — | `capabilities[].scope` | 用户提到的行业；没提到就留空数组，**不要默认填「互联网」** |
| — | `capabilities[].soft` | 走句式库的软能力标 `true`；标了 `true` 就必须有量化结果 |

**硬约束**（违反会直接导致第 6 步占比失真）：

- 每层**至少 1 项**，总数 **5–16 项**——少于 5 项结论不可信，多于 16 项说明把技能当能力了
- 每个 `lv` 必须有依据；写不出依据就降到 `lv=1`，不要靠「我觉得我挺强」
- `soft: true` 的项**必须**用句式库重写，不接受「沟通能力强」这类无验收标准的表述

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
包含 `jd`/`req`/`keywords`/`resume`/`build`/`repos` 六段，外加 `capabilities`（能力要求）
与脚本生成的 `matrix`（能力矩阵）。

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

**能力拆解**（第 6 步的输入，写进每个岗位的 `capabilities`）：

从 `req` 逐条抽出能力，映射到 16 项目录，分 `must` / `plus` 两组：

- `lv` 按 JD 要求定级：提到即会用 = `2` / 要求熟练 = `3` / 要求主导或负责 = `4`
- `w` 按招聘措辞定权重：必须 = `3` / 优先 = `2` / 加分 = `1`
- **覆盖率必须 ≥ 80% 的 `req`**——拆完回头数一遍，还有哪些要求没落到任何能力项上，补进去
- **跨轨道岗位必须含 ≥1 项 `L3`**：转型场景下元能力是唯一不被折价的资产，缺了它第 6 步会误判成「完全不适合」
- `must` 建议 2–4 项、`plus` 1–3 项。`must` 全填 10 项等于没有优先级

拆完后**不要手写 `matrix`**——那是 `capability_matrix.py` 的输出，手写必然与算法漂移，
且页面不会报错，只是数字错了（详见 `references/data-contract.md` 的 ⚠️ 提示）。

### 阶段三之二：调用工具做确定性校验（**不要凭感觉打分**）

本 skill 自带确定性工具。**凡是能用工具算的，不要让模型估。**

```bash
# 1) 岗位匹配打分 —— 确定性，可复现，不烧 token
python scripts/match_score.py --profile profile.json --jobs jobs.json

# 2) 招聘页正文 → 结构化 JD
python scripts/split_jd.py --raw page.txt --out jd.json

# 3) 三级能力矩阵 → 写回 jobs.json 的 jobs[].matrix（第 6 步的唯一数据源）
python scripts/capability_matrix.py --profile profile.json --jobs jobs.json --merge
```

第 3 条是**必跑**的：不跑 `--merge`，页面第 6 步会整体消失（不是报错，是静默降级成五步版本）。
想单独看某个岗位的诊断结果，去掉 `--merge` 直接输出到 stdout：

```bash
python scripts/capability_matrix.py --profile profile.json --job one.json
python scripts/capability_matrix.py --profile profile.json --jobs jobs.json --scene switch   # 强制按转型场景判
```

**为什么必须用工具而不是让模型判断**：

| 环节 | 交给谁 | 原因 |
| --- | --- | --- |
| 岗位匹配打分、关键词命中 | **`match_score.py`** | 同一输入必须同一分数。模型会漂移（今天 73 明天 68），用户立刻失去信任 |
| JD 切分 | **`split_jd.py`** | 段落识别是规则问题，模型容易过度发挥 |
| 三层占比、命中率、迁移折价、场景判定 | **`capability_matrix.py`** | 占比必须三项和恒为 100（最大余额法），模型算不出这个约束 |
| 能力归属改判、经历改写、二创引导、面试建议 | **大模型** | 这才是真正需要判断力的地方 |

### 阶段四：生成 HTML

```bash
python scripts/render.py <jobs.json> <输出.html> --title "标题" --subtitle "副标题"
```

`render.py` 会产出单文件页面（内联 CSS/JS，零外部请求，双击即开）。
可选参数：
- `--theme sci|art|biz` 切换设计系统与文案语气（默认按 jobs 中的 track 自动判定）
- `--no-repo` 跳过第 4 步（当二创来源确实检索不到时）
- `--no-cap` 跳过第 6 步（当用户确实不做能力盘点时，强制输出五步版本）

**第 6 步是条件渲染的**：只要任一岗位的 `capabilities` 有内容，页面自动变成六步法；
反之退回五步法，且**老数据渲染结果与 v1.1 逐字节一致**（向后兼容，不要为了兼容去改老 JSON）。

**视觉层由 token 驱动，不要手改色值。** 三个轨道各绑一套真实设计系统：

| 轨道 | 设计系统 | 气质 |
| --- | --- | --- |
| `sci` 理工科 | Vercel | 近白画布 / 近黑文字 / 单一蓝强调 |
| `art` 人文社科 | Editorial | 暖纸面 / 衬线标题 / 赭石强调 |
| `biz` 经管商科 | Stripe | 白底 / 藏青文字 / 紫罗兰强调 |

产出物里所有颜色都写成 `var(--token)`，定义在 `scripts/design_systems.py`。
换主题 = 改一处映射；细则与来源许可见 `references/design-systems.md`。

**三层能力色是同色相三级明度**（`--cap-l1` / `--cap-l2` / `--cap-l3`，由 `accent` 向 `surface`
按 0 / 30% / 55% 混色派生），不是三个语义色。因为三层是同一光谱的三段而非三种无关类型；
`design_systems.py` 有自检断言三档明度必须严格递增，改混色比例跑一次就知道有没有破。

**改样式前先读 `references/design-systems.md` 的「有意不做的事」一节**——
首屏渐变光晕、双品牌色、满屏大圆角、到处都有的卡片投影、结构件里的彩色 emoji
都是被主动去掉的 AI 味，不要加回来。

生成后**必须验证**（见下），不要声称「应该能跑」。

### 阶段五：验证与交付

1. **结构自检**：`python scripts/render.py --selftest <jobs.json>` 校验数据完整性
   （会同时校验 `capabilities` 的枚举值与 `matrix` 的形状，`share` 三项和不为 0/100 会报警告）
2. **真实渲染验收**：按 `references/verify-render.md` 用无头 Chrome 截图，肉眼确认
   - 岗位切换器可切换且内容联动
   - 第 5 步勾选状态能持久化（localStorage）
   - **第 6 步占比条三段之和为 100%**（若显示 14% / 72% / 14% 这类，加起来必须是整 100；
     出现 `0%` 段是正常的——说明用户该层没有能力项）
   - **切到第二个岗位后，缺口清单与迁移路径必须跟着变**。这是最容易出的静默 bug：
     `renderStep6()` 若只挂在 `renderAll` 没挂 `switchJob`，页面不报错，但第 6 步永远停在第一个岗位
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

**换平台不影响行为**，因为重活都交给了脚本：打分、JD 切分、能力矩阵都是确定性代码，
agent 只负责理解意图与改写表达。

## 资源索引

| 文件 | 何时读 |
| --- | --- |
| `references/search-recipes.md` | 阶段二，开始联网检索前 |
| `references/track-dimensions.md` | 阶段一，判定学科轨道后；文理科能力维度库（只管「怎么练」） |
| `references/capability-tiers.md` | 阶段一第 4 轮 + 阶段三拆能力前；三级判定树、16 项目录、分级标准、句式库 |
| `references/resume-rules.md` | 阶段三，生成定制简历前 |
| `references/rework-matrix.md` | 阶段三，推荐项目与二创来源时 |
| `references/data-contract.md` | 阶段三，构造 jobs.json / profile.json 时；含完整字段定义与示例 |
| `references/design-systems.md` | 阶段四，改视觉前；token schema、换主题方法、anti-AI-slop 清单 |
| `references/verify-render.md` | 阶段五，验证 HTML 时 |
| `references/portability.md` | 需要装到别的 agent 平台时；跨平台兼容矩阵与坑位 |
| `scripts/render.py` | 阶段四，生成 HTML |
| `scripts/design_systems.py` | 阶段四，视觉层 token（**改配色/字体/间距只改这里**） |
| `scripts/match_score.py` | 阶段三，岗位匹配打分（**确定性，别让模型估**） |
| `scripts/split_jd.py` | 阶段三之二，招聘页正文 → 结构化 JD |
| `scripts/capability_matrix.py` | 阶段三之二，三级能力矩阵算分（**第 6 步唯一数据源**） |
| `scripts/install.py` | 跨平台安装：`--detect` 探测 / `--target` 安装 |
| `examples/profile.sample.json` | 阶段一/三，`profile.json` 的可运行样例 |
| `examples/jobs.sample.json` | 阶段三，六步法 `jobs.json` 的可运行样例 |

## 工具速查

| 命令 | 作用 | 自检 |
| --- | --- | --- |
| `match_score.py --profile p.json --jobs j.json` | 批量打分并排序 | `--selftest` |
| `match_score.py --profile p.json --job one.json` | 单岗位打分 | — |
| `split_jd.py --raw page.txt` | 招聘页正文 → JD/要求 | `--selftest` |
| `split_jd.py --raw page.txt --out jd.json` | 同上，写入文件 | — |
| `capability_matrix.py --profile p.json --jobs j.json --merge` | 算三级矩阵并写回 `jobs[].matrix` | `--selftest` |
| `capability_matrix.py --profile p.json --job one.json --scene switch` | 单岗位诊断，可强制场景 | — |
| `render.py jobs.json out.html` | 生成引导页 | `--selftest` |
| `render.py jobs.json out.html --no-cap` | 强制五步版本 | — |
| `design_systems.py` | 视觉 token 自检（齐全性 + 混色算法 + 三层明度） | 直接运行 |
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
- **把 `L2` 通用能力写成 `L1` 垂类深度** → 最常见的判断错误。「跨 3 个行业协调过团队」仍是 `L2`，
  因为验收方还是通用管理标尺，不是行业内部专家。写错会让第 6 步的占比失真，
  用户会误以为自己「垂类很强」，投递时主打错层。拿不准就回到那一问：
  **这份证据的验收方是谁？** 行业内部 → `L1`，通用标尺 → `L2`。
- **手写 `matrix`** → 它是 `capability_matrix.py` 的输出，手写必然与算法漂移，
  且页面不会报错。数据永远是「profile + capabilities → 脚本 → matrix」。
- **声称已验证但没截图** → 本环境 Chrome headless 可用，务必实际渲染确认。

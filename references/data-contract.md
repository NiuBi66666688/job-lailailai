# jobs.json 数据契约

`scripts/render.py` 的唯一输入。阶段三产出此文件，阶段四消费它。
`scripts/capability_matrix.py` 会向 `jobs[].matrix` 写入能力矩阵（阶段三之二）。

## 顶层结构

```json
{
  "meta": {
    "title": "从大三到字节 Seed — 简历蜕变六步法",
    "subtitle": "已抓取 7 个实习岗位的完整职位描述与职位要求（官网原文）…",
    "track": "sci",
    "generatedAt": "2026-10-11",
    "company": "字节跳动 Seed",
    "capabilityCatalog": "1.0",
    "linkLabel": "岗位数据来自公开招聘平台，抓取于 2026-10-11"
  },
  "stats": [
    { "n": "7", "l": "目标岗位" },
    { "n": "6", "l": "蜕变步骤" }
  ],
  "jobs": [ /* 见下 */ ],
  "global": {
    "roadmap": [ /* 见下 */ ],
    "checklist": [ "每条支持 **加粗** 语法" ],
    "strategy": [ { "t": "标题", "d": "说明" } ]
  }
}
```

## job 对象

```json
{
  "id": "A258400A",
  "idx": 1,
  "title": "AI搜索Agent算法实习生",
  "company": "字节跳动",
  "project": "Seed大模型人才实习招聘",
  "city": "上海",
  "category": "研发 - 算法",
  "track": "sci",
  "direction": "agent",
  "directionLabel": "Agent / 搜索应用型",
  "url": "https://jobs.bytedance.com/...",
  "source": "jobs.bytedance.com",
  "fetchedAt": "2026-10-11",

  "jd":  ["1、下一代搜索问答Agent构建：…"],
  "req": ["1、2028届及以后本科及以上学历在读；…"],
  "keywords": ["RAG", "Agent架构", "Prompt Engineering"],

  "resume": {
    "positioning": "定位：会落地 RAG+Agent 全链路、能用评测数字说话的算法工程师。",
    "summary": "[待补充] 人工智能专业在读（2028届），具备…",
    "skills": [
      { "k": "RAG / 检索", "v": "LangChain、Faiss 向量检索、BM25【待补充】", "hit": true }
    ],
    "projects": [
      { "name": "【示例写法·待替换为你自己的项目】企业知识库 RAG 问答 Agent",
        "star": "S 级（技术栈：Python / LangChain / Faiss）",
        "body": "背景：…\n动作：…\n结果：[待补充：准确率 X%→Y%]" }
    ],
    "match": [
      ["熟悉 RAG / Agent 架构", "技能栏第 1、2 项 + RAG 问答 Agent 项目"],
      ["RL / Reward Model", "[待补充]：如做过 DPO / 奖励模型，务必单独列出"]
    ]
  },

  "build": [
    { "p": "P0", "t": "端到端 RAG + Agent 问答系统（可开源）",
      "d": "含混合召回、重排序、溯源、评测集。验收：自建评测集上有可复现的准确率数字。" }
  ],

  "repos": [
    { "name": "infiniflow/ragflow", "star": "92.0k", "lang": "Go/Python",
      "tag": "RAG+Agent 引擎", "why": "…",
      "fork": ["为它接入你自己的混合召回策略并做消融", "…"],
      "mode": "C", "accept": "PR 被合并 或 消融实验有可复现结论" }
  ],

  "capabilities": {
    "must": [
      { "id": "L1-TECH-BUILD", "name": "检索链路工程落地", "tier": "L1", "cat": "tech", "lv": 3, "w": 3 },
      { "id": "L2-DATA-LITERACY", "name": "评测指标设计", "tier": "L2", "cat": "data", "lv": 2, "w": 3 }
    ],
    "plus": [
      { "id": "L2-WRITTEN-EXPR", "name": "技术文档写作", "tier": "L2", "cat": "content", "lv": 2, "w": 1 }
    ]
  },

  "matrix": { /* 由 capability_matrix.py 生成，禁止手写 */ }
}
```

### `capabilities` · 岗位能力要求（可选）

缺省时不生成第 6 步，页面回落到五步版本。写了就必须按 `capability-tiers.md` 的判定树定级。

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `capabilities.must` | ✅ | 硬性要求，1–8 项。`w` 缺省 3 |
| `capabilities.plus` | — | 加分项，`w` 缺省 1 |
| `[].id` | ✅ | 取自 16 项目录；无法归类时用 `X-<slug>` |
| `[].name` | ✅ | 该岗位语境下的中文名（可与目录名不同） |
| `[].tier` | ✅ | `L1` / `L2` / `L3`，指**该岗位对这一能力的定位** |
| `[].cat` | ✅ | 能力族：`tech data content research business compliance process people meta` |
| `[].lv` | ✅ | 岗位要求熟练度 0–4 |
| `[].w` | — | 权重 1–3：必须=3 / 优先=2 / 加分=1 |

### `matrix` · 能力矩阵（**只允许脚本生成**）

> ⚠️ **不要手写这个字段。** 它必须由 `scripts/capability_matrix.py --merge` 产出。
> 手写会与 `profile.json` 的自评漂移，导致页面上的三层占比、缺口、路径互相矛盾。
> 渲染层只校验形状（`share` 三项和为 100），不校验业务正确性——写错了不会报错，只会悄悄错。

```bash
python scripts/capability_matrix.py --profile profile.json --jobs jobs.json --merge --out jobs.json
```

产出结构（节选，完整见脚本 `analyze()` 的返回）：

```json
"matrix": {
  "jobId": "A258400A", "jobTitle": "AI搜索Agent算法实习生",
  "score": 68, "coverage": 83, "migrateRate": 17,
  "scene": { "code": "B", "label": "非垂类宽泛择业", "hint": "…", "reason": "匹配度 68 ≥ 55…" },
  "tiers": { "L1": { "hit": 55, "req": 4, "ok": 2, "gap": 2, "weight": 0.5 },
             "L2": { "hit": 72, "req": 3, "ok": 2, "gap": 1, "weight": 0.3 },
             "L3": { "hit": 40, "req": 1, "ok": 0, "gap": 1, "weight": 0.2 } },
  "share": { "L1": 30, "L2": 50, "L3": 20 },
  "columns": { "L1": [ { "id": "…", "name": "…", "def": "…", "lv": 2,
                         "scope": ["互联网"], "evidence": "…", "hit": true } ],
               "L2": [], "L3": [] },
  "hit": [], "transfer": [], 
  "gap": [ { "id": "…", "name": "…", "tier": "L1", "need": 3, "have": 0,
             "w": 3, "weeks": 9, "lever": "无同族底座，需从零建立" } ],
  "paths": [ { "title": "…", "from": "…", "to": "…", "action": "…", "weeks": 6 } ],
  "source": { "profileHash": "9f2c1ab4", "catalogVersion": "1.0" }
}
```

`source.profileHash` 与当前 profile 不符时，`render.py --selftest` 只给 WARN——说明自评改过但没重算，页面数字已过期。

## 字段规则

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `meta.track` | ✅ | `sci`/`art`/`biz`，决定主题配色与文案 |
| `jobs[].track` | — | 缺省继承 `meta.track` |
| `jobs[].id` | ✅ | 岗位编号或自定义 slug，用于切换与去重 |
| `jobs[].jd` / `req` | ✅ | 数组，元素为**原文**句子（含「1、」编号前缀） |
| `jobs[].keywords` | ✅ | 10–15 个，来自 JD/req 抽词 |
| `jobs[].resume.match` | ✅ | `[[要求, 证据], …]`；证据含 `[待补充]` 时渲染成红色 |
| `jobs[].build[].p` | ✅ | 仅 `P0`/`P1`/`P2` |
| `jobs[].repos` | — | 为空时该岗位跳过第 4 步 |
| `jobs[].major` / `grade` | — | 专业 / 届别，渲染进简历抬头；缺省显示 `[专业]` `[届别]` |
| `jobs[].capabilities.must` | — | 缺省时该岗位跳过第 6 步（整页回落到五步版本） |
| `jobs[].capabilities[].tier` | ✅ | 仅 `L1`/`L2`/`L3`，非法值渲染前报 ERROR |
| `jobs[].capabilities[].lv` | ✅ | 0–4 整数；超出范围钳制并给 WARN |
| `jobs[].capabilities[].w` | — | 1–3，缺省 2 |
| `jobs[].matrix` | — | **只允许 `capability_matrix.py --merge` 生成**，禁止手写 |

## profile.json 数据契约

阶段一（含第 4 轮能力盘点）的产物，`capability_matrix.py` 的输入。与 `jobs.json` 分开存放。

```json
{
  "track": "sci",
  "intent": "broad",
  "targetIndustry": "",
  "capabilityMeta": {
    "assessedAt": "2026-10-18",
    "method": "self-report-4pt",
    "catalogVersion": "1.0"
  },
  "capabilities": [
    { "id": "L1-TECH-BUILD", "name": "技术方案落地", "tier": "L1", "cat": "tech",
      "lv": 2, "scope": ["互联网"], "soft": false,
      "evidence": "[待补充：上线服务与 QPS]" },
    { "id": "L2-DATA-LITERACY", "name": "数据素养与指标解读", "tier": "L2", "cat": "data",
      "lv": 3, "scope": ["互联网", "零售", "金融"], "soft": false,
      "evidence": "课程项目：用 SQL 完成 12 万条订单的漏斗分析，定位第 3 天流失拐点" },
    { "id": "L3-JOB-DECONSTRUCT", "name": "岗位能力拆解", "tier": "L3", "cat": "meta",
      "lv": 2, "scope": ["互联网"], "soft": false,
      "evidence": "拆过 10 份 JD，能指出 1 条「JD 没写但实际必需」的能力" }
  ]
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `intent` | ✅ | `vertical`（只投本行业）/ `broad`（本行业为主、兼顾相邻）/ `switch`（明确跨行业转型）。驱动择业场景判定 |
| `targetIndustry` | — | `intent=switch` 时必填，用于生成迁移路径文案 |
| `capabilities` | ✅ | 5–16 项，且每层至少 1 项 |
| `capabilities[].id` | ✅ | 取自 16 项目录；自定义用 `X-<slug>` |
| `capabilities[].tier` | ✅ | 用户自评层级；被 Phase 3 校正后以校正值为准 |
| `capabilities[].cat` | ✅ | 缺省按 `id` 查目录补齐 |
| `capabilities[].lv` | ✅ | 0–4。**说不出依据的一律记 1**，不允许凭感觉给 3 |
| `capabilities[].scope` | — | 该能力已应用的行业，至少 1 个；这是跨行业迁移的唯一实证 |
| `capabilities[].evidence` | ✅ | 允许 `[待补充]`，但 `lv≥3` 时不允许为空占位 |
| `capabilities[].soft` | — | 软能力标记。`true` 时证据必须走 `capability-tiers.md` 第四节的句式库 |
| `capabilityMeta.method` | — | `self-report-4pt`（自评）/ `inferred`（从经历推断） |

## 占位符约定（render.py 自动处理）

| 写法 | 渲染效果 |
| --- | --- |
| `[待补充：说明]` 或 `[待补充]` | 红色高亮 `placeholder` |
| `【示例写法】` 或 `【示例写法·说明】` | 紫色高亮 `example` |

所以**不要**在数据里手写 HTML 标签来高亮——交给渲染器。

## 最小可用示例

```json
{
  "meta": { "title": "新媒体运营实习 · 简历蜕变", "track": "art", "generatedAt": "2026-10-11" },
  "stats": [{ "n": "3", "l": "目标岗位" }],
  "jobs": [{
    "id": "op-001", "idx": 1, "title": "新媒体运营实习生",
    "city": "北京", "category": "市场 - 内容", "track": "art",
    "url": "https://example.com/job/1", "fetchedAt": "2026-10-11",
    "jd":  ["1、负责公众号日常内容策划与撰写；"],
    "req": ["1、本科在读，中文、新闻、传播相关专业优先；"],
    "keywords": ["内容策划", "公众号", "选题", "数据复盘"],
    "resume": {
      "positioning": "定位：能独立完成从选题到分发的图文内容，有真实传播数据的候选人。",
      "summary": "[待补充] 新闻学在读（2028届）。",
      "skills": [{ "k": "内容生产", "v": "选题策划、长文写作、多平台改写【待补充】", "hit": true }],
      "projects": [{ "name": "【示例写法】校园人物专栏",
        "star": "作品集（工具：公众号 / 秀米）",
        "body": "背景：…\n动作：…\n结果：[待补充：篇数 / 阅读量 / 转载数]" }],
      "match": [["内容策划与撰写", "校园人物专栏 + 技能栏第 1 项"]]
    },
    "build": [{ "p": "P0", "t": "上线个人作品集站点", "d": "验收：有线上链接，含 5 篇代表作" }],
    "repos": [],
    "capabilities": {
      "must": [
        { "id": "L1-CONTENT-PROD", "name": "图文内容生产", "tier": "L1", "cat": "content", "lv": 3, "w": 3 },
        { "id": "L2-DATA-LITERACY", "name": "传播数据复盘", "tier": "L2", "cat": "data", "lv": 2, "w": 2 }
      ]
    }
  }],
  "global": {
    "roadmap": [{ "phase": "第 1-2 周", "title": "定位与地基", "items": ["…"] }],
    "checklist": ["每篇作品都有**真实数据**（阅读/转发/转化）"],
    "strategy": [{ "t": "一岗一版", "d": "…" }]
  }
}
```

## 自检

```bash
python scripts/render.py --selftest jobs.json      # 数据契约 + 占位符规范
python scripts/capability_matrix.py --selftest     # 算分逻辑（11 条断言）
```

`render.py --selftest` 会检查：meta/jobs 必填字段、`p` 取值合法性、`match` 二元组、
`fork` 是否为空数组、keywords 数量、占位符写法是否规范、`capabilities` 的 tier/lv/w 枚举、
`matrix.share` 三项和是否为 100。
**有 ERROR 必须修完再渲染**；WARNING 可酌情忽略（例如 `profileHash` 不符，说明自评改过但没重算）。

完整链路：

```bash
python scripts/capability_matrix.py --profile profile.json --jobs jobs.json --merge --out jobs.json
python scripts/render.py --selftest jobs.json
python scripts/render.py jobs.json out.html --theme sci
```

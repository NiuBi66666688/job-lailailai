# jobs.json 数据契约

`scripts/render.py` 的唯一输入。阶段三产出此文件，阶段四消费它。

## 顶层结构

```json
{
  "meta": {
    "title": "从大三到字节 Seed — 简历蜕变五步法",
    "subtitle": "已抓取 7 个实习岗位的完整职位描述与职位要求（官网原文）…",
    "track": "sci",
    "generatedAt": "2026-10-11",
    "company": "字节跳动 Seed",
    "linkLabel": "岗位数据来自公开招聘平台，抓取于 2026-10-11"
  },
  "stats": [
    { "n": "7", "l": "目标岗位" },
    { "n": "5", "l": "蜕变步骤" }
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
  ]
}
```

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
    "repos": []
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
python scripts/render.py --selftest jobs.json
```

会检查：meta/jobs 必填字段、`p` 取值合法性、`match` 二元组、
`fork` 是否为空数组、keywords 数量、占位符写法是否规范。
**有 ERROR 必须修完再渲染**；WARNING 可酌情忽略。

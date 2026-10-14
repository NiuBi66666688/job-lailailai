# 联网检索配方

配合 `multi-search-engine` skill 使用。目标：**拿到真实岗位的 JD 与职位要求原文**，而不是凭标题猜。

## 一、引擎分工

| 查询语言 | 推荐引擎 |
| --- | --- |
| 中文 | 百度、Bing CN（`cn.bing.com/search?q=X&ensearch=0`）、360（`so.com`）、搜狗、微信搜一搜（`wx.sogou.com`）、神马 |
| 英文 | Google、Google HK、DuckDuckGo、Brave、Startpage |

- 每个查询**并行打 2–3 个引擎**做交叉验证；单一引擎可能漏掉或给出过时快照。
- 引擎返回 403/429 时，先抓该引擎首页取会话 Cookie，等 2 秒重试一次，仍失败则换引擎。
- 请求间加 1–2 秒延时，别把引擎打崩。

## 二、招聘站定向（`site:` 是效率关键）

泛搜「算法实习生 招聘」几乎全是中介聚合页。定向到招聘站才拿得到结构化 JD。

### 综合招聘平台
```
site:zhipin.com       BOSS直聘
site:zhaopin.com      智联招聘
site:51job.com        前程无忧
site:lagou.com        拉勾（互联网）
site:liepin.com       猎聘（中高端）
site:nowcoder.com     牛客（校招/实习/面经）
```

### 校招 / 实习官方入口
```
site:jobs.bytedance.com      字节跳动
site:join.qq.com             腾讯校招
site:careers.tencent.com     腾讯社招
site:talent.alibaba.com      阿里
site:campus.alibaba.com      阿里校招
site:hr.baidu.com            百度
site:job.meituan.com         美团
site:jobs.bilibili.com       B站
site:campus.163.com          网易
site:join.huawei.com         华为
site:campus.xiaomi.com       小米
site:careers.jd.com          京东
site:zhaopin.pinduoduo.com   拼多多
site:jobs.mihoyo.com         米哈游
site:careers.kuaishou.com    快手
```

### 国企 / 事业单位 / 公务员（文科重要通道）
```
site:gongkao.com             公考类
site:offcn.com               中公
site:zhaopin.com 国企
site:chinahr.com             央企人才网
<省名>.gov.cn 人事考试
site:*.edu.cn 就业信息网
```

### 高校就业网（校招信息最全，且含宣讲会）
```
site:*.edu.cn 就业 招聘 <专业关键词> 2028届
site:*.edu.cn 校园招聘 宣讲会 <行业>
```

## 三、查询模板

### 岗位发现（第一轮，宽口径）
```
<岗位关键词> <城市> 2028届 实习 招聘
<岗位名称> site:jobs.bytedance.com
<专业名> 对口岗位 校招
```
时效：`&tbs=qdr:m`（近一月）；校招旺季用 `qdr:w`。

### JD 提取（第二轮，定点爆破）
检索到详情页后，直接抓正文；抓不到就换该岗位的镜像页（牛客/看准/BOSS 同岗位）：
```
"<岗位全称>" 职位描述 职位要求
"<岗位全称>" 任职要求 site:nowcoder.com
```

### 行业/趋势（用于写简历的「定位」段）
```
<行业> 2026 人才需求 趋势
<岗位> 技能要求 变化
```

### 文科专用
```
新媒体运营 实习 职位要求 <城市>
内容策划 校招 site:zhipin.com
人力资源 管培生 招聘要求
市场品牌 实习生 site:zhaopin.com
```

### 英文岗（外企/海外）
```
"<job title>" internship 2026 requirement
"<job title>" site:linkedin.com/jobs
"<job title>" job description site:greenhouse.io
```

## 四、正文抓取与降级

1. **优先**：直接抓岗位详情页正文（`web_fetch`），提取 JD 与职位要求**原文**。
2. **反爬降级**（返回 SPA 壳 HTML / 无正文 / 403）：
   - 换 Bing CN 或 360 的**缓存快照**
   - 换该岗位在牛客、看准网、职友集上的**镜像描述**
   - 用平台公开的岗位摘要
3. **拿不到就如实标注**。写：
   `未检索到该岗位完整 JD，以下为平台摘要，需人工赴官网确认`，并把来源 URL 附上。

## 五、结果记录格式

每个岗位抓到后，立刻落盘成结构（供 `data-contract.md` 使用）：

```json
{
  "title": "岗位全称",
  "company": "公司名",
  "city": "上海",
  "category": "研发 - 算法",
  "track": "sci",
  "url": "https://.../detail",
  "source": "jobs.bytedance.com",
  "fetchedAt": "2026-10-11",
  "jd": ["1、...", "2、..."],
  "req": ["1、...", "2、..."],
  "keywords": ["RAG", "Agent架构"]
}
```

`track` 取值：`sci`（理工科）/ `art`（人文社科）/ `biz`（经管商科）。
它决定简历维度库、项目推荐形态与 HTML 主题。

## 六、检索伦理

- 遵守各站 `robots.txt` 与 ToS；本流程只做人岗信息检索，不做批量爬取。
- 请求间隔 1–2 秒；不并发轰炸单一域名。
- 岗位信息标注来源与抓取日期，提醒用户以官网实时发布为准。

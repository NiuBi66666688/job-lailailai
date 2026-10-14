# 视觉层：设计系统与 token

本 skill 的产出 HTML 长什么样，由 `scripts/design_systems.py` 决定。
`render.py` 只写结构（选择器 + 布局），**不写色值**——所有颜色、字体、间距、
圆角、投影都通过 `var(--token)` 引用。这样换主题不会漏改，也不会出现
「改了主色但某个角标还是旧色」这类问题。

## 一、三个轨道各绑一套设计系统

| 轨道 | 设计系统 | 视觉气质 | 依据 |
| --- | --- | --- | --- |
| `sci` 理工科 | **Vercel** | 近白画布、近黑文字（#171717）、单一蓝强调（#0070f3）、以阴影充当描边 | 工程感的克制表达，适合技术岗语境 |
| `art` 人文社科 | **Editorial** | 暖纸面（#fbf7f0）、衬线标题（Georgia/宋体）、赭石强调（#9a5a2f） | 出版物的编排语言，作品集/调研报告语境 |
| `biz` 经管商科 | **Stripe** | 白底、藏青文字（#061b31）、紫罗兰强调（#533afd）、多层蓝调投影 | 金融基础设施的专业感 |

选型不是随手挑的：三套系统的**明度层级、字重习惯、投影逻辑互不相同**，
切换轨道时用户能明显感到「这是给另一类岗位做的」，而不是同一套皮换个色。

> 轨道未指定或非法时回退 `sci`。

## 二、token schema

所有 token 定义在 `design_systems.py`，渲染时编译进产出的 `:root` 块。

| 组 | token |
| --- | --- |
| 表面 | `--bg` `--surface` `--surface-2` `--surface-translucent` |
| 文字 | `--fg` `--fg-2` `--muted` `--meta` |
| 描边 | `--border` `--border-soft` |
| 强调 | `--accent` `--accent-on` `--accent-hover` `--accent-active` `--accent-soft` `--accent-ink` |
| 语义 | `--success` `--warn` `--danger`（各带 `-soft` / `-ink`） |
| 优先级 | `--p0` `--p1` `--p2`（各带 `-soft` / `-ink`） |
| 字体 | `--font-display` `--font-body` `--font-mono` |
| 字号 | `--text-xs` … `--text-4xl` |
| 行高/字距 | `--leading-body` `--leading-tight` `--tracking-display` |
| 间距 | `--space-1` `--space-2` `--space-3` `--space-4` `--space-5` `--space-6` `--space-8` `--space-12` |
| 区块节奏 | `--section-y-desktop` `--section-y-tablet` `--section-y-phone` |
| 圆角 | `--radius-sm` `--radius-md` `--radius-lg` `--radius-pill` |
| 投影 | `--elev-flat` `--elev-ring` `--elev-raised` |
| 焦点 | `--focus-ring` |
| 动效 | `--motion-fast` `--motion-base` `--ease-standard` |
| 版心 | `--container-max` `--container-gutter-desktop/tablet/phone` |

### `-soft` 与 `-ink` 是什么

上游 schema 只给实色。软底色（浅底徽章、提示条）与软底上的文字色是**派生**的：

- `-soft`：角色色以 8% 混进主题 `--surface`，保证浅底与底色同源而不是各调各的。
- `-ink`：角色色朝主题 `--fg` 混 35%。角色色直接当文字压在自身浅底上对比度不够
  （Vercel 的 `--warn` 是亮黄 #eab308，白字压上去几乎看不见），混向主题文字色
  等于在浅色主题里「压深」，且仍与主题同源。

## 三、换主题 / 加主题

改**一处**即可，不用碰 `render.py`：

```python
# design_systems.py
TRACK_SYSTEM = {"sci": "vercel", "art": "editorial", "biz": "stripe"}
```

要换某轨道用的设计系统，改这个映射；要加全新轨道，在 `SYSTEMS` 里登记一个
返回 token 字典的函数，再加一条映射。`render.py` 的 `THEMES` 只管文案
（轨道叫什么、第 4 步叫什么），与视觉解耦。

改完跑自检：

```bash
python scripts/design_systems.py     # token 齐全性 + oklab 计算正确性
```

## 四、有意不做的事（anti-AI-slop）

视觉改造遵循「避免 AI 味」的通用规范，以下是被**主动去掉**的东西：

| 去掉 | 原因 |
| --- | --- |
| 首屏紫蓝渐变 + 右上角径向光晕 | 没有产品理由的装饰性渐变，是最典型的 AI 味 |
| 双品牌色（`--brand` + `--brand2`） | 一套系统只留一个强调色，双色渐变是廉价感来源 |
| 到处都有的卡片投影 | 阴影只在真正需要抬升的地方出现（吸顶导航、吐司） |
| 满屏大圆角（14px 全局） | 改为按 token 分档：4–6px 输入/徽章、8px 卡片、12px 大容器 |
| 章节号的渐变方块 | 改为描边方块 + 单色字形 |
| 激活态填充药丸 | 改为强调色下划线，更克制 |
| 结构件里的彩色 emoji | 章节号/卡片头/提示条统一单色字形（`◎ 图 检 策 § ⓘ`），与既有 `描/求/历/✓` 一致 |

保留的例外：页脚祝语里的 🚀。整页唯一的暖色人情味，放在收尾处是有意的。

## 五、工程约束（不要破坏）

1. **零第三方依赖**。`design_systems.py` 只用标准库。oklab 混色是自己实现的
   （与 CSS `color-mix(in oklab, …)` 同算法），这样做的原因是把 `color-mix()`
   的浏览器支持要求（Chrome 111+ / Safari 16.2+）从产出物上摘掉——
   产出物要「双击即开」，不该赌浏览器版本。
2. **产出物零外部请求**。不引 CDN 字体、不引外部 CSS/JS。字体走系统栈 +
   中文字体回退（无衬线接 PingFang / 微软雅黑，衬线接宋体），
   否则中文会掉到默认字体、版面立刻变差。
3. **颜色只写一次**。新增样式一律 `var(--token)`；需要新颜色时先在
   `design_systems.py` 派生，不要在 `render.py` 里写死 hex。

## 六、来源与许可

三套 token 取自 **OpenDesign 设计系统包**，上游仓库
<https://github.com/nexu-io/open-design>，路径 `design-systems/{vercel,editorial,stripe}/`，
许可 **Apache-2.0**。

- 本地适配（`design_systems.py`）在文件头逐条记录了与上游的差异。
- 产出 HTML 的 `<style>` 顶部会写入一段署名注释，保留来源与许可声明
  （Apache-2.0 要求的 attribution）。这段注释只在查看源码时可见，
  不影响页面观感——如果你希望页面上也显示署名，可以自行加一行页脚。

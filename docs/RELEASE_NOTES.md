# v1.1.0 · 三套设计系统 + 跨平台安装修复

## 新增

- **token 驱动的视觉层**：新增 `scripts/design_systems.py`。颜色、字体、间距、圆角、投影
  全部收敛为 token，`render.py` 只写结构。换主题 = 改一处映射。
- **三套真实设计系统**（来自 [OpenDesign](https://github.com/nexu-io/open-design)，Apache-2.0）：

  | 轨道 | 设计系统 | 气质 |
  | --- | --- | --- |
  | `sci` 理工科 | Vercel | 近白画布 / 近黑文字 / 单一蓝强调 |
  | `art` 人文社科 | Editorial | 暖纸面 / 衬线标题 / 赭石强调 |
  | `biz` 经管商科 | Stripe | 白底 / 藏青文字 / 紫罗兰强调 |

- **纯 Python oklab 混色**：构建期预解析 `color-mix(in oklab, …)`，
  产出物不再要求 Chrome 111+ / Safari 16.2+。
- `references/design-systems.md`、`examples/jobs.sample.json`。

## 修复

- `install.py` 自检在非默认安装位置必然失败（会卡住「迁移到异地」这个主场景）。
- `references/verify-render.md` 探针注入代码的悬空 `<script>` 导致误判页面有 bug。

## 去 AI 味

移除首屏渐变光晕、双品牌色、满屏大圆角、到处都有的卡片投影；
结构件里的彩色 emoji 改为单色字形。

## 安装

```bash
git clone https://github.com/NiuBi66666688/job-lailailai.git
cd job-lailailai
python verify.py                 # 先验收
python scripts/install.py --target all --link
```

或下载下方迁移包 zip，解压到任意目录后同样先跑 `python verify.py`。

**零第三方依赖**，不需要执行 `pip install`。

# job-lailailai（求职简历蜕变引导）

本目录是一个**可移植 agent skill**。**完整流程见同目录下的 `SKILL.md`**，此处只做指针与摘要。

> 只认 `AGENTS.md` 的平台（Cursor / Codex / 部分自研 agent 环境）读到这里就够了；
> 认 `SKILL.md` 的平台（WorkBuddy / Claude Code / Qoder CN）会自动加载完整流程。

## 一句话

把招聘网站的真实岗位 JD，翻译成用户可执行的简历蜕变方案：
**岗位定锚 → 定制简历 → 项目成果 → 二创来源 → 蜕变路线**，
最终产出单文件可视化 HTML 引导页（顶部岗位切换器，切换时前四步内容联动）。

## 核心要点

1. **问答先行**。先用 `AskUserQuestion` 采集专业 / 届别 / 技能 / 目标（一轮最多 4 题），再检索、再生成。
2. **数据真实可溯源**。岗位来自联网检索，每条记录 `url` / `source` / `fetchedAt`；查不到就写「未检索到」。
3. **确定性优先**。岗位匹配打分、JD 切分用 `scripts/` 下的脚本算，**不要让模型估**（同一输入必须同一分数）。
4. **文理双轨**。人文社科同样要走招聘站检索，不许默认推代码项目。
5. **视觉只改 token 层**。页面样式由 `scripts/design_systems.py` 驱动，三个轨道各绑一套真实设计系统；
   **不要在 `render.py` 里手写色值**，要新颜色先在 token 层派生。
6. **产出必须验证**。渲染后用无头浏览器截图肉眼确认，不要声称「应该能跑」。

## 目录

```
SKILL.md                完整工作流（必读）
AGENTS.md               本文件：给只认 AGENTS.md 的平台做指针
README.md               使用说明（安装 / 配置 / 调用 / 常见问题）
CHANGELOG.md            版本记录
LICENSE                 Apache-2.0
NOTICE                  上游 OpenDesign 设计系统的署名
requirements.txt        依赖声明（零第三方依赖）
verify.py               落地后一键验收（先跑这个）
scripts/match_score.py  岗位匹配打分（确定性，可复现）
scripts/split_jd.py     招聘页正文 → 结构化 JD
scripts/design_systems.py  视觉层 token（Vercel / Editorial / Stripe 三套）
scripts/render.py       生成单文件 HTML 引导页
scripts/install.py      跨平台安装（--detect / --target）
references/             按需读的细则：检索配方 / 维度库 / 简历规则 / 二创矩阵 /
                        数据契约 / 设计系统 / 渲染验证 / 跨平台坑位
examples/jobs.sample.json  可运行样例数据（验证链路用）
examples/demo.html         构建产物：样例渲染出的单文件页面
docs/PUBLISH.md         发布上线指南（含每步骤配图要求）
docs/preview/           三主题在线预览页（GitHub Pages 入口在 docs/index.html）
docs/images/            README 与 PUBLISH 的配图
```

> Release 里附带的迁移包 zip 内另有 `MANIFEST.txt`（SHA256 清单），用于校验传输无损。
> 仓库本体不含该文件——Git 本身已提供完整性保证，且清单会在每次改动后失效。


## 极简调用

```bash
python scripts/match_score.py --profile profile.json --jobs jobs.json
python scripts/split_jd.py --raw page.txt --out jd.json
python scripts/render.py jobs.json out.html
python verify.py            # 迁移后先跑这个
```

详细参数与完整流程：**读 `SKILL.md`**。

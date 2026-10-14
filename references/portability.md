# 跨平台安装与兼容矩阵

本 skill 采用「**单一真源目录 + 各平台软链/复制**」的通用格式，不绑定任何一家 agent 平台。
同一份 `SKILL.md + scripts/ + references/` 可以被 WorkBuddy、Claude Code、Cursor、Codex、Qoder CN
等主流编码/通用 agent 读取，因为它们共享同一套事实标准：**Markdown 指令文件 + 可执行脚本**。

## 一、为什么能通用

三类平台的能力差异只体现在「入口文件名」和「脚本调用方式」，指令本身是同一份：

| 关注点 | 事实标准 | 说明 |
| --- | --- | --- |
| 指令载体 | Markdown（YAML frontmatter） | 所有主流 agent 都读 Markdown 作为系统指令 |
| 能力扩展 | 本地可执行脚本 | Python/Node 在任意平台都在 |
| 元信息 | `name` + `description` | frontmatter 已被广泛识别 |
| 触发方式 | 描述匹配 / 显式 @ 引用 | 描述写清楚即可自动触发 |

**唯一真正的差异是入口文件名**，因此本目录额外提供 `AGENTS.md` 作为「信号放大器」，
内容是 `SKILL.md` 的指针 + 核心要点摘要，供只认 `AGENTS.md` 的平台自动加载。

## 二、各平台入口对照

| 平台 | 入口文件名 | 默认位置 | 加载方式 |
| --- | --- | --- | --- |
| **WorkBuddy** | `SKILL.md` | `~/.workbuddy-ai/skills/<name>/` | 自动扫描 + 描述匹配 |
| **Claude Code** | `SKILL.md` | `~/.claude/skills/<name>/` | 自动扫描 + 描述匹配 |
| **Cursor** | `AGENTS.md` 或 `.cursor/rules/*.mdc` | 项目根 / `~/.cursor/` | 规则文件常驻上下文 |
| **Codex (OpenAI)** | `AGENTS.md` | 项目根 / `~/.codex/` | 自动读取 AGENTS.md |
| **Qoder CN** | `SKILL.md` 或 `AGENTS.md` | `~/.qoder/skills/` / 项目根 | 自动扫描 + 描述匹配 |

> 不同版本的目录名可能微调，安装脚本会自动探测已存在的目录并给出建议路径。

## 三、一键安装

`scripts/install.py` 负责把本目录复制到目标平台，或仅生成软链（推荐软链，改一处全平台生效）。

```bash
# 1) 探测本机已安装哪些平台
python scripts/install.py --detect

# 2) 安装到指定平台（复制模式，最稳）
python scripts/install.py --target claude-code
python scripts/install.py --target cursor

# 3) 安装到全部探测到的平台（软链模式，推荐）
python scripts/install.py --target all --link

# 4) 只生成 AGENTS.md 指针（Cursor / Codex 用）
python scripts/install.py --target codex --agents-md --dest ./my-project
```

参数说明：

| 参数 | 作用 |
| --- | --- |
| `--detect` | 只探测，不写任何文件。列出探测结果与推荐路径 |
| `--target` | `workbuddy` / `claude-code` / `cursor` / `codex` / `qoder` / `all` |
| `--link` | 建软链而非复制（改源目录即全平台生效；Windows 需开发者模式） |
| `--dest` | 项目级安装的目标路径（默认用户级目录） |
| `--agents-md` | 额外在目标目录生成 `AGENTS.md` |
| `--force` | 目标已存在时覆盖 |

## 四、各平台调用脚本的方式

**所有平台完全一致**，都是调用本地 Python：

```bash
python scripts/match_score.py --profile profile.json --jobs jobs.json
python scripts/split_jd.py --raw page.txt --out jd.json
python scripts/render.py jobs.json out.html
```

注意：
- 若平台所在环境无 `python` 命令，用 `python3` 或 `py`；`install.py --detect` 会一并探测。
- 脚本**零第三方依赖**（纯标准库），不需要 `pip install` 任何东西，这是刻意的设计——
  跨平台最大的坑就是依赖安装失败。
- Windows 下路径含空格务必加引号。

## 五、跨平台常见坑

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 平台没自动触发本 skill | `description` 未命中，或未放入被扫描的目录 | 用 `install.py --detect` 确认路径；或在对话中显式 @ 引用 |
| Cursor / Codex 认不出 | 它们优先读 `AGENTS.md` | 加 `--agents-md` 生成指针文件 |
| Windows 建软链报错 | 未开启开发者模式 | 改用复制模式（去掉 `--link`） |
| 脚本找不到 | 用了相对路径但 cwd 不对 | 用绝对路径调用；或先 `cd` 到 skill 目录 |
| 中文乱码 | Windows 控制台默认 GBK | 脚本已强制 UTF-8 输出；若仍乱码执行 `chcp 65001` |
| 换了平台后行为不一致 | 各平台上下文预算不同，长 reference 可能被截断 | 核心要点已内联进 `SKILL.md`，reference 是「按需读」，截断不影响主线 |

## 六、设计取舍（为什么不做平台专属版本）

1. **不写平台专属 prompt**：一旦分叉就有维护成本，且各平台迭代快，专属版很快过期。
2. **重活交给脚本**：打分、JD 切分全部是确定性 Python，
   agent 只负责「理解意图 + 改写表达」。这样换任何平台，核心行为都不变。
3. **`AGENTS.md` 只做指针不做副本**：避免两份指令漂移。指针里写明「完整流程见 SKILL.md」。

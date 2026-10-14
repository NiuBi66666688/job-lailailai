#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 job-lailailai 安装到各主流 agent 平台。

设计目标：单一真源目录 -> 各平台入口，避免多份指令漂移。
零第三方依赖，纯标准库。
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

# Windows 控制台默认 GBK，强制 UTF-8 以免中文报错
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SKILL_NAME = "job-lailailai"
HERE = Path(__file__).resolve().parent.parent  # skill 根目录

HOME = Path.home()

# 平台 -> 候选安装目录（按优先级）。第一个命中的即为探测结果。
PLATFORM_DIRS = {
    "workbuddy": [
        HOME / ".workbuddy-ai" / "skills",
    ],
    "claude-code": [
        HOME / ".claude" / "skills",
        HOME / ".config" / "claude" / "skills",
    ],
    "qoder": [
        HOME / ".qoder" / "skills",
        HOME / ".qoder-cn" / "skills",
        HOME / ".qoderwork" / "skills",
    ],
    "cursor": [
        HOME / ".cursor" / "rules",
    ],
    "codex": [
        HOME / ".codex",
    ],
}

# 各平台是否需要同时生成 AGENTS.md（它们优先读这个）
NEEDS_AGENTS_MD = {"cursor", "codex"}

AGENTS_MD_TEMPLATE = """# job-lailailai（求职简历蜕变引导）

本目录是一个可移植 agent skill。**完整流程见同目录下的 `SKILL.md`**，此处只做指针与摘要。

## 一句话

把招聘网站的真实岗位 JD，翻译成用户可执行的简历蜕变方案：岗位定锚 → 定制简历 → 项目成果
→ 二创来源 → 蜕变路线，最终产出单文件可视化 HTML 引导页。

## 核心要点

1. **问答先行**。先采集专业/届别/技能/目标，再检索、再生成。
2. **数据真实可溯源**。岗位来自联网检索，记录 url / source / fetchedAt。
3. **确定性优先**。打分、JD 切分用 `scripts/` 下的脚本算，不要让模型估。
4. **文理双轨**。人文社科同样要走招聘站检索，不许默认推代码项目。

## 目录

```
SKILL.md                完整工作流（必读）
scripts/match_score.py  岗位匹配打分（确定性）
scripts/split_jd.py     招聘页正文 → 结构化 JD
scripts/render.py       生成单文件 HTML 引导页
scripts/install.py      跨平台安装
references/             按需读的细则（检索配方/维度库/简历规则/二创矩阵/数据契约/验证）
```

## 极简调用

```bash
python scripts/match_score.py --profile profile.json --jobs jobs.json
python scripts/split_jd.py --raw page.txt --out jd.json
python scripts/render.py jobs.json out.html
```

详细参数与完整流程：**读 `SKILL.md`。**
"""


def detect():
    """探测各平台是否存在，返回 {platform: (exists, primary_dir)}。"""
    result = {}
    for plat, dirs in PLATFORM_DIRS.items():
        primary = dirs[0]
        found = any(d.exists() for d in dirs)
        result[plat] = (found, primary)
    return result


def cmd_detect():
    res = detect()
    print("平台探测结果：\n")
    width = max(len(p) for p in res)
    for plat, (found, primary) in res.items():
        mark = "[已安装]" if found else "[未发现]"
        print(f"  {plat.ljust(width)}  {mark}  -> {primary}")
    print(f"\nPython: {sys.executable}")
    print(f"Skill 源目录: {HERE}")
    avail = [p for p, (f, _) in res.items() if f]
    if avail:
        print(f"\n建议：--target all 将安装到 {len(avail)} 个已发现平台：{', '.join(avail)}")
    else:
        print("\n未探测到任何已知平台目录。可用 --dest 指定自定义路径。")
    return 0


def _resolve_target_dir(plat, dest):
    if dest:
        return Path(dest) / SKILL_NAME
    dirs = PLATFORM_DIRS[plat]
    for d in dirs:
        if d.exists():
            return d / SKILL_NAME
    return dirs[0] / SKILL_NAME


def _write_agents_md(target_parent, force):
    p = Path(target_parent) / "AGENTS.md"
    if p.exists() and not force:
        print(f"  [跳过] AGENTS.md 已存在（--force 可覆盖）：{p}")
        return
    p.write_text(AGENTS_MD_TEMPLATE, encoding="utf-8")
    print(f"  [写入] {p}")


def _same_path(a, b):
    """两个路径是否**字面指向同一处**（解析软链后比较）。

    用于判断「target 是不是源目录本身」。注意：必须用 realpath 比较，
    但**不能**用它判断「target 是别处指向源目录的软链」——那属于正常安装结果。
    """
    try:
        ra = Path(os.path.realpath(str(a)))
        rb = Path(os.path.realpath(str(b)))
        return os.path.normcase(str(ra)) == os.path.normcase(str(rb))
    except Exception:
        return False


def _is_source_itself(target):
    """target 是否**就是**源目录本身（而非指向源目录的软链）。

    判据：realpath 相同 **且** target 自己不是软链。
    指向源目录的软链也满足 realpath 相同，但它必须返回 False ——
    那是合法的安装结果，不该被跳过。
    """
    if target.is_symlink():
        return False
    return _same_path(target, HERE)


def install_one(plat, link, dest, agents_md, force):
    target = _resolve_target_dir(plat, dest)
    parent = target.parent

    # ⚠️ 护栏：绝不能把源目录自己当成安装目标。
    # 否则 --force 会先 rmtree(源目录)、再建一个指向自身的软链，
    # 导致源码被删除且变成自引用死循环（v1.0 真实踩过这个坑）。
    # 只拦截「target 字面就是源目录」，不拦截「软链指向源目录」。
    if _is_source_itself(target):
        print(f"  [跳过] 目标就是源目录自身，无需安装：{target}")
        print("         （该平台正是 skill 的安装位置，无需重复安装）")
        return True

    try:
        parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"  [失败] 无法创建目录 {parent}：{e}")
        return False

    if target.exists() or target.is_symlink():
        if not force:
            print(f"  [跳过] 目标已存在（--force 覆盖）：{target}")
        else:
            if target.is_symlink() or target.is_file():
                target.unlink()
            else:
                shutil.rmtree(target)

    if target.exists() or target.is_symlink():
        pass
    elif link:
        try:
            os.symlink(HERE, target, target_is_directory=True)
            print(f"  [软链] {target}  ->  {HERE}")
        except (OSError, NotImplementedError) as e:
            print(f"  [降级] 软链失败（{e}），改为复制")
            try:
                shutil.copytree(
                    HERE, target,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"),
                )
                print(f"  [复制] {target}")
            except Exception as e2:
                print(f"  [失败] 复制也失败：{e2}")
                return False
    else:
        try:
            shutil.copytree(
                HERE, target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"),
            )
            print(f"  [复制] {target}")
        except Exception as e:
            print(f"  [失败] 复制失败：{e}")
            return False

    if agents_md or plat in NEEDS_AGENTS_MD:
        _write_agents_md(parent, force)
    return True


def cmd_install(args):
    if args.target == "all":
        targets = [p for p, (f, _) in detect().items() if f]
        if args.dest:
            # 指定了 dest 就用全部平台名，但都落到同一 dest（去重）
            targets = list(PLATFORM_DIRS.keys())
        if not targets:
            print("未探测到任何平台。请用 --target <平台名> 或 --dest <路径> 显式指定。")
            return 1
    else:
        targets = [args.target]

    print(f"安装 {SKILL_NAME} 到 {len(targets)} 个目标：\n")
    ok = 0
    for plat in targets:
        print(f"[{plat}]")
        if args.dest:
            if install_one(plat, args.link, args.dest, args.agents_md, args.force):
                ok += 1
            break  # dest 模式只装一次
        if install_one(plat, args.link, None, args.agents_md, args.force):
            ok += 1
        print()
    print(f"完成：{ok}/{len(targets)} 成功。")
    if not args.link:
        print("提示：改动源目录不会同步到副本。用 --link 可获得「改一处全平台生效」。")
    return 0


def selftest():
    print("=== install.py 自检 ===")
    checks = []

    # 1) 源目录存在且含 SKILL.md
    ok1 = (HERE / "SKILL.md").exists()
    checks.append(("源目录含 SKILL.md", ok1, str(HERE / "SKILL.md")))

    # 2) 平台表非空且结构正确
    ok2 = bool(PLATFORM_DIRS) and all(
        isinstance(v, list) and len(v) > 0 for v in PLATFORM_DIRS.values()
    )
    checks.append(("平台目录表结构正确", ok2, f"{len(PLATFORM_DIRS)} 个平台"))

    # 3) detect 返回完整
    res = detect()
    ok3 = set(res.keys()) == set(PLATFORM_DIRS.keys())
    checks.append(("detect 覆盖全部平台", ok3, ", ".join(res.keys())))

    # 4) AGENTS.md 模板含关键要点与指针
    ok4 = "问答先行" in AGENTS_MD_TEMPLATE and "SKILL.md" in AGENTS_MD_TEMPLATE
    checks.append(("AGENTS.md 模板含要点与指针", ok4, ""))

    # 5) 路径解析不炸
    try:
        p = _resolve_target_dir("workbuddy", None)
        ok5 = p.name == SKILL_NAME
        info = str(p)
    except Exception as e:
        ok5, info = False, str(e)
    checks.append(("目标路径解析正确", ok5, info))

    # 6) 【回归】护栏：目标 == 源目录 必须被识别出来
    #    v1.0 曾因缺少这个护栏，--force 把源目录 rm 掉再建自引用软链，导致源码丢失。
    ok6 = _same_path(HERE, HERE) and _same_path(HERE, HERE / ".")
    checks.append(("护栏能识别「目标==源目录」", ok6, "防自引用删除"))

    # 7) 不同路径必须判为不同（否位置换不生效）
    ok7 = not _same_path(HERE, HERE.parent / "__definitely_not_here__")
    checks.append(("护栏不误判不同路径", ok7, ""))

    # 8) 【回归】自装场景：无论本 skill 装在哪个目录，把「源目录自己」当目标
    #    都必须被护栏识别并跳过（v1.0 曾在此处自毁）。
    #    ⚠️ 这里**不能**断言「workbuddy 默认路径 == 源目录」——迁移包、项目级安装、
    #    自定义 --dest 时二者本就不同，那样会让自检在任何非原始位置必然失败
    #    （v1.1 踩过：打包到 build/ 后自检挂掉）。
    ok8 = _is_source_itself(HERE)
    at_wb_default = _same_path(_resolve_target_dir("workbuddy", None), HERE)
    checks.append(
        ("自装场景已被护栏覆盖（与安装位置无关）", ok8,
         "会安全跳过而非自毁；当前" + ("位于 workbuddy 默认路径"
                                  if at_wb_default else "不在 workbuddy 默认路径（正常）")),
    )

    allok = True
    for name, ok, info in checks:
        print(f"[{'✓' if ok else '✗'}] {name}" + (f"  -> {info}" if info else ""))
        allok = allok and ok
    print("\n" + ("[✓] 全部自检通过" if allok else "[✗] 存在失败项"))
    return 0 if allok else 1


def main():
    ap = argparse.ArgumentParser(
        description="把 job-lailailai 安装到各主流 agent 平台",
    )
    ap.add_argument("--detect", action="store_true", help="只探测已安装平台，不写文件")
    ap.add_argument(
        "--target",
        choices=list(PLATFORM_DIRS.keys()) + ["all"],
        help="目标平台",
    )
    ap.add_argument("--link", action="store_true", help="建软链而非复制（推荐）")
    ap.add_argument("--dest", help="自定义安装根目录（项目级安装）")
    ap.add_argument("--agents-md", action="store_true", help="额外生成 AGENTS.md")
    ap.add_argument("--force", action="store_true", help="目标已存在时覆盖")
    ap.add_argument("--selftest", action="store_true", help="运行自检")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if args.detect:
        return cmd_detect()
    if not args.target:
        ap.print_help()
        return 0
    return cmd_install(args)


if __name__ == "__main__":
    sys.exit(main())

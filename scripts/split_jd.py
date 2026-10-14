#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""招聘页正文 → 结构化 JD / 任职要求。

按段落小标题切分招聘页面抓下来的正文，把「岗位职责」与「任职要求」分开，
输出可直接喂给 render.py 的 JSON。零第三方依赖。

用法：
    python split_jd.py --raw page.txt
    python split_jd.py --raw page.txt --out jd.json
    python split_jd.py --selftest
"""

import argparse
import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# 章节小标题：出现这些词说明后面是「职责」或「要求」
JD_PAT = re.compile(r"岗位职责|工作内容|职位描述|你将负责|职责描述|responsibilit", re.I)
REQ_PAT = re.compile(r"任职要求|职位要求|岗位要求|任职资格|我们希望你|requirement", re.I)

# 列表符号：编号（1. 1、1) ）或圆点（- • · *）
BULLET = re.compile(r"^[0-9]+[.、)）]\s*|^[-•·*]\s*|^\([0-9]+\)\s*")


def split_jd(raw_text):
    """把招聘页正文切成 {"jd": [...], "req": [...]}。

    规则：
    - 遇到「岗位职责」小标题 → 后续行归入 jd
    - 遇到「任职要求」小标题 → 后续行归入 req
    - 小标题行本身不计入内容
    - 两种标题都还没出现时，行暂存为 other；若全程无标题，则整体归入 jd
    """
    lines = [s.strip() for s in re.split(r"\n+", raw_text or "") if s.strip()]
    jd, req, other = [], [], []
    where = ""

    for line in lines:
        if REQ_PAT.search(line):
            where = "req"
            # 小标题可能同行带内容（如「任职要求：1、本科…」），把冒号后的部分留下
            tail = _tail_after_colon(line)
            if tail:
                req.append(tail)
            continue
        if JD_PAT.search(line):
            where = "jd"
            tail = _tail_after_colon(line)
            if tail:
                jd.append(tail)
            continue

        text = BULLET.sub("", line).strip()
        if not text:
            continue
        if where == "jd":
            jd.append(text)
        elif where == "req":
            req.append(text)
        else:
            other.append(text)

    # 没识别出任何标题时，把正文整体当职责，避免丢内容
    if not jd and not req and other:
        jd = other

    return {"jd": jd, "req": req}


def _tail_after_colon(line):
    """取出「小标题：正文」里冒号后面的正文部分；没有则返回空串。"""
    m = re.split(r"[：:]\s*", line, maxsplit=1)
    if len(m) == 2:
        return BULLET.sub("", m[1]).strip()
    return ""


def selftest():
    errs = []

    # 1) 标准双标题切分
    raw = (
        "内容运营实习生\n"
        "岗位职责：\n"
        "1. 负责内容选题策划与日常更新\n"
        "2. 分析内容数据并输出复盘报告\n"
        "任职要求：\n"
        "1. 本科及以上在读\n"
        "2. 有新媒体运营经验者优先\n"
    )
    r = split_jd(raw)
    if len(r["jd"]) != 2:
        errs.append(f"jd 应为 2 条，实为 {len(r['jd'])}：{r['jd']}")
    else:
        print("[✓] JD 切分正确：jd", len(r["jd"]), "条 / req", len(r["req"]), "条")
    if len(r["req"]) != 2:
        errs.append(f"req 应为 2 条，实为 {len(r['req'])}：{r['req']}")

    # 2) 页面乱序（要求在前）也要正确归类
    raw2 = "任职要求：\n- 中文相关专业\n岗位职责：\n- 负责公众号日常编辑\n"
    r2 = split_jd(raw2)
    if "负责公众号日常编辑" not in " ".join(r2["jd"]):
        errs.append("乱序页面归类错误")
    else:
        print("[✓] 乱序页面正确归类")

    # 3) 无标题时整体归入 jd（不丢内容）
    raw3 = "- 负责选题策划\n- 负责数据复盘\n"
    r3 = split_jd(raw3)
    if len(r3["jd"]) != 2:
        errs.append(f"无标题兜底失败：{r3}")
    else:
        print("[✓] 无标题正文兜底归入 jd")

    # 4) 小标题同行带内容
    raw4 = "任职要求：本科及以上，新闻相关专业优先\n"
    r4 = split_jd(raw4)
    if "本科及以上" not in " ".join(r4["req"]):
        errs.append(f"同行内容未提取：{r4}")
    else:
        print("[✓] 「标题：内容」同行内容已提取")

    # 5) 空输入健壮
    try:
        r5 = split_jd("")
        if r5["jd"] or r5["req"]:
            errs.append("空输入应返回空列表")
        else:
            print("[✓] 空输入健壮")
    except Exception as e:
        errs.append(f"空输入崩溃：{e}")

    if errs:
        print("\n[✗] 自检失败：")
        for e in errs:
            print("   -", e)
        return 1
    print("\n[✓] 全部自检通过")
    return 0


def main():
    ap = argparse.ArgumentParser(description="招聘页正文 → 结构化 JD / 任职要求")
    ap.add_argument("--raw", help="招聘页正文 txt 文件")
    ap.add_argument("--out", help="输出 JSON 路径（默认打印到 stdout）")
    ap.add_argument("--selftest", action="store_true", help="运行自检")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if not args.raw:
        ap.print_help()
        return 0

    try:
        with open(args.raw, encoding="utf-8") as f:
            raw = f.read()
    except Exception as e:
        print(f"[✗] 读取失败：{e}", file=sys.stderr)
        return 1

    result = split_jd(raw)
    out = json.dumps(result, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[✓] 已写入 {args.out}")
    else:
        print(out)
    print(f"\n--- 切分结果：职位描述 {len(result['jd'])} 条 / 职位要求 {len(result['req'])} 条 ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
match_score.py — 岗位匹配打分（确定性，Agent 工具）

这是本 Agent 的**规则层**。模型只该出现在需要判断力的环节（改写措辞、给建议），
不该做算术。同一份输入必须得到同一个分数——模型会漂移（今天 73 明天 68），
用户会立刻失去信任，且每次打分都烧 token。

用法（Agent 直接调）：
  python match_score.py --profile profile.json --job job.json
  python match_score.py --profile profile.json --jobs jobs.json      # 批量打分排序
  python match_score.py --selftest                                   # 自检

输入 schema 见 references/data-contract.md。
"""

import argparse
import json
import re
import sys


# ---------------------------------------------------------------------------
# 核心打分
# ---------------------------------------------------------------------------
def _skill_name(s):
    """技能项归一化为字符串。兼容多种写法：
    - "Python"                        （纯字符串，最自然的手写格式）
    - {"n": "Python"}                 （data-contract 的简写）
    - {"name": "Python", ...}         （啰嗦写法）
    - {"skill": "Python"} / {"value": ...}
    返回空串表示该项无效，调用方应跳过。
    """
    if isinstance(s, str):
        return s.strip()
    if isinstance(s, dict):
        for k in ("n", "name", "skill", "value", "label", "title"):
            v = s.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return ""


def _skill_list(raw):
    """把 profile.skills 归一化成字符串列表，容忍 None/字符串/字典混合。"""
    if not raw:
        return []
    if isinstance(raw, str):
        # 允许逗号/顿号/斜杠分隔的一整串
        return [p.strip() for p in re.split(r"[,，、/|]", raw) if p.strip()]
    if isinstance(raw, dict):
        raw = [raw]
    out = []
    for s in raw:
        n = _skill_name(s)
        if n:
            out.append(n)
    return out


def _exp_blob(e):
    """把一条经历归一化成可检索文本。兼容 dict 与纯字符串。"""
    if isinstance(e, str):
        return e
    if not isinstance(e, dict):
        return str(e)
    keys = ("stack", "bg", "action", "result", "title", "detail", "desc", "name")
    return " ".join(str(e.get(k, "")) for k in keys)


def covered(keyword, skills, experiences):
    """关键词是否被档案覆盖（技能名 或 经历正文）。"""
    if not keyword:
        return False
    for s in skills:
        if keyword in s or s in keyword:
            return True
    for e in experiences:
        blob = _exp_blob(e)
        if keyword in blob:
            return True
    return False


def match_job(profile, job):
    """对一个岗位打分。纯函数，无随机，无时间依赖。"""
    profile = profile or {}
    job = job or {}

    skills = _skill_list(profile.get("skills"))
    exps = profile.get("experiences") or []
    if isinstance(exps, dict):
        exps = [exps]

    kws = job.get("kw") or job.get("keywords") or []
    if isinstance(kws, dict):
        kws = list(kws.keys())
    # 关键词项也可能是 dict（如 {"n": "Python"}），统一取名字
    kws = [_skill_name(k) or (k if isinstance(k, str) else "") for k in kws]
    kws = [k for k in kws if k]
    if not kws:
        text = " ".join((job.get("jd") or []) + (job.get("req") or []))
        kws = extract_keywords(text)

    hit = [k for k in kws if covered(k, skills, exps)]
    miss = [k for k in kws if k not in hit]
    rate = round(len(hit) / max(1, len(kws)) * 100)

    hard = job.get("hard") or []
    if isinstance(hard, str):
        hard = [hard]
    hard = [(_skill_name(h) or h) for h in hard if isinstance(h, (str, dict))]
    hard = [h for h in hard if h]
    hard_hit = [h for h in hard if covered(h, skills, exps)]
    hard_miss = [h for h in hard if h not in hard_hit]

    # 命中率 55% + 硬性要求 35% → 再叠加奖励，钳制到 20-99
    base = rate * 0.55 + (len(hard_hit) / max(1, len(hard) or 1)) * 35
    bonus = len(hit) * 3 + len(exps) * 2 + min(15, len(skills) * 2)
    score = max(20, min(99, round(base + bonus)))

    if score >= 80:
        verdict = "强匹配"
    elif score >= 65:
        verdict = "较匹配"
    elif score >= 45:
        verdict = "有机会，需补短板"
    else:
        verdict = "差距较大"

    return {
        "jobId": job.get("id", ""),
        "jobTitle": job.get("title", "未命名岗位"),
        "score": score,
        "rate": rate,
        "verdict": verdict,
        "hit": hit,
        "miss": miss,
        "hardMiss": hard_miss,
        "summary": (
            "岗位「{t}」匹配分 {s}（{v}）。命中 {h}/{n} 个关键词：{hit}。"
            "缺口：{miss}。未满足硬性要求：{hm}。用户经历 {e} 条，技能 {sk} 项。"
        ).format(
            t=job.get("title", "未命名岗位"), s=score, v=verdict,
            h=len(hit), n=len(kws),
            hit="、".join(hit[:12]) or "无",
            miss="、".join(miss[:12]) or "无",
            hm="、".join(hard_miss[:6]) or "无",
            e=len(exps), sk=len(skills),
        ),
    }


def extract_keywords(text, limit=16):
    """从 JD 抽关键词：以英文/技术词为主。"""
    words = re.findall(r"[A-Za-z][A-Za-z+#./0-9]{1,20}", text or "")
    stop = {"and", "the", "for", "with", "you", "are", "our", "will", "able",
            "good", "team", "have", "has", "not", "but", "can", "all", "any",
            "its", "their", "from", "this", "that", "such", "including"}
    out, seen = [], set()
    for w in words:
        lw = w.lower()
        if len(w) < 3 or lw in stop or lw in seen:
            continue
        seen.add(lw)
        out.append(w)
    return out[:limit]


# ---------------------------------------------------------------------------
# 自检
# ---------------------------------------------------------------------------
def selftest():
    profile = {
        "majorKey": "sci",
        "skills": [{"n": "Python", "lv": 4}, {"n": "PyTorch", "lv": 3},
                   {"n": "RAG", "lv": 2}],
        "experiences": [{
            "title": "知识库问答", "stack": "Python/LangChain/Faiss",
            "bg": "文档检索不准", "action": "构建混合召回+重排序",
            "result": "准确率提升到 81%",
        }],
    }
    job = {
        "id": "A1", "title": "AI搜索Agent算法实习生",
        "jd": ["设计基于LLM的端到端智能问答系统"],
        "req": ["熟悉PyTorch，有RAG与Agent架构经验"],
        "kw": ["RAG", "Python", "PyTorch", "Agent", "Faiss", "vLLM"],
        "hard": ["RAG", "PyTorch"],
    }

    errs = []
    r = match_job(profile, job)
    print("打分结果：", r["score"], r["verdict"])
    print("summary：", r["summary"])

    # 1) 确定性：连跑 5 次分数必须完全一致
    scores = {match_job(profile, job)["score"] for _ in range(5)}
    if len(scores) != 1:
        errs.append(f"确定性失败：分数漂移 {scores}")
    else:
        print("[✓] 确定性：连跑 5 次分数一致")

    # 2) 空档案不崩溃
    try:
        r0 = match_job({}, job)
        if not (20 <= r0["score"] <= 99):
            errs.append(f"空档案分数越界：{r0['score']}")
        else:
            print("[✓] 空档案健壮，分数", r0["score"])
    except Exception as e:
        errs.append(f"空档案崩溃：{e}")

    # 3) 分数永远在边界内
    for p in ({}, profile, {"skills": [{"n": "x"}] * 50, "experiences": [{}] * 50}):
        try:
            s = match_job(p, job)["score"]
            if not (20 <= s <= 99):
                errs.append(f"分数越界 {s}")
        except Exception as e:
            errs.append(f"极端档案崩溃：{e}")
    if not any("越界" in e or "崩溃" in e for e in errs):
        print("[✓] 分数边界钳制正常（20-99）")

    # 4) 技能越多分数不应下降（单调性）
    p2 = json.loads(json.dumps(profile))
    p2["skills"].append({"n": "Agent", "lv": 4})
    if match_job(p2, job)["score"] < r["score"]:
        errs.append("单调性失败：增加相关技能后分数反而下降")
    else:
        print("[✓] 单调性：增加相关技能分数不降")

    # 5) 【回归】技能写成纯字符串列表也必须能算
    #    v1.0 硬编码 s.get("n")，遇到 ["Python", ...] 直接 AttributeError 崩溃。
    try:
        p_str = {"skills": ["Python", "PyTorch", "RAG"], "experiences": []}
        rs = match_job(p_str, job)
        if not (20 <= rs["score"] <= 99):
            errs.append(f"字符串技能分数越界：{rs['score']}")
        else:
            print("[✓] 字符串技能列表可正常打分，分数", rs["score"])
    except Exception as e:
        errs.append(f"字符串技能列表崩溃：{e}")

    # 6) 技能写成逗号分隔的一整串也要能用
    try:
        p_flat = {"skills": "Python, PyTorch、RAG", "experiences": []}
        rf = match_job(p_flat, job)
        print("[✓] 分隔符字符串技能可解析，命中", len(rf["hit"]), "项")
    except Exception as e:
        errs.append(f"分隔符技能串崩溃：{e}")

    # 7) 经历写成纯字符串也要能用
    try:
        p_exp = {"skills": [], "experiences": ["用 Python 做过 RAG 检索项目"]}
        re_ = match_job(p_exp, job)
        print("[✓] 字符串经历可解析，命中", len(re_["hit"]), "项")
    except Exception as e:
        errs.append(f"字符串经历崩溃：{e}")

    # 8) 关键词写成 dict 列表也要能用
    try:
        job_dict_kw = dict(job)
        job_dict_kw["kw"] = [{"n": "RAG"}, {"n": "Python"}, {"n": "Faiss"}]
        rd = match_job(profile, job_dict_kw)
        print("[✓] dict 形式关键词可解析，命中", len(rd["hit"]), "项")
    except Exception as e:
        errs.append(f"dict 关键词崩溃：{e}")

    if errs:
        print("\n[x] 自检失败：")
        for e in errs:
            print("   ", e)
        return 1
    print("\n[✓] 全部自检通过")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="岗位匹配打分（确定性）")
    ap.add_argument("--profile", help="用户档案 JSON")
    ap.add_argument("--job", help="单个岗位 JSON")
    ap.add_argument("--jobs", help="岗位数组 JSON（批量打分并排序）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if not args.profile:
        print("[x] 需要 --profile", file=sys.stderr)
        return 1

    with open(args.profile, encoding="utf-8") as f:
        profile = json.load(f)

    if args.job:
        with open(args.job, encoding="utf-8") as f:
            job = json.load(f)
        print(json.dumps(match_job(profile, job), ensure_ascii=False, indent=2))
        return 0

    if args.jobs:
        with open(args.jobs, encoding="utf-8") as f:
            data = json.load(f)
        jobs = data.get("jobs") if isinstance(data, dict) else data
        results = sorted((match_job(profile, j) for j in jobs),
                         key=lambda x: -x["score"])
        print(json.dumps(results, ensure_ascii=False, indent=2))
        print(f"\n--- 排序概览（{len(results)} 个岗位）---")
        for i, r in enumerate(results, 1):
            print(f"{i:>2}. [{r['score']:>2}] {r['verdict']}  {r['jobTitle']}")
        return 0

    print("[x] 需要 --job 或 --jobs", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

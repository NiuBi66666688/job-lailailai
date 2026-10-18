#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三级能力矩阵 · 垂类专属（L1）/ 非垂类通用（L2）/ 跨类迁移（L3）。

把 profile.json 的能力盘点与 jobs.json 的能力要求做**确定性**比对，产出：
三层占比、各层命中率、缺口清单（含补齐工期）、迁移路径建议、择业场景判定。

设计原则：同一输入必须同一份额。所有阈值都是模块常量，所有计算无随机、无时间依赖。
本脚本只做算术，不做判断——「这项能力属于哪层」由 capability-tiers.md 的判定树决定，
本脚本只认 id 与 cat。

用法：
    python capability_matrix.py --profile p.json --jobs jobs.json --merge --out jobs.json
    python capability_matrix.py --profile p.json --job job.json [--out m.json]
    python capability_matrix.py --selftest

退出码：0 成功 / 1 输入错误 / 2 自检失败
"""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

CATALOG_VERSION = "1.0"

# ----------------------------------------------------------------------------
# 能力目录（唯一权威）。references/capability-tiers.md 是本表的文档化呈现，
# verify.py 的 check_catalog_sync() 断言两者 id 集合一致。
# ----------------------------------------------------------------------------
CATALOG = {
    # ── L1 垂类专属 ──────────────────────────────────────────────────────
    "L1-TECH-BUILD": {
        "name": "技术方案落地与系统交付", "tier": "L1", "cat": "tech",
        "def": "把模糊需求转为可运行系统，并对延迟、可用性、成本等工程指标负责",
    },
    "L1-DATA-MODEL": {
        "name": "数据建模与指标口径设计", "tier": "L1", "cat": "data",
        "def": "定义业务指标口径、维度模型与可复现的数据链路",
    },
    "L1-CONTENT-PROD": {
        "name": "内容生产与叙事结构", "tier": "L1", "cat": "content",
        "def": "从选题到分发的完整内容生产，对传播结果负责",
    },
    "L1-RESEARCH-DESIGN": {
        "name": "研究设计与证据链构建", "tier": "L1", "cat": "research",
        "def": "用抽样、访谈、实验等方法产出可被质疑与复现的结论",
    },
    "L1-COMMERCIAL-ANALYSIS": {
        "name": "商业分析与估值建模", "tier": "L1", "cat": "business",
        "def": "拆解商业问题并建模，输出可支撑决策的量化判断",
    },
    "L1-COMPLIANCE": {
        "name": "合规与风险审查", "tier": "L1", "cat": "compliance",
        "def": "按特定法域与监管口径识别、分级、留痕风险",
    },
    # ── L2 非垂类通用 ────────────────────────────────────────────────────
    "L2-STRUCT-PROBLEM": {
        "name": "结构化问题拆解", "tier": "L2", "cat": "process",
        "def": "把模糊问题拆成可验证的假设与可执行的动作",
    },
    "L2-DATA-LITERACY": {
        "name": "数据素养与指标解读", "tier": "L2", "cat": "data",
        "def": "读得懂数据、算得对指标、说得清结论的边界",
    },
    "L2-PROJECT-DELIVERY": {
        "name": "项目推进与交付管理", "tier": "L2", "cat": "process",
        "def": "在范围、时间、资源约束下把事推到交付",
    },
    "L2-STAKEHOLDER": {
        "name": "跨部门沟通与干系人管理", "tier": "L2", "cat": "people",
        "def": "识别利益相关方、对齐预期、收敛分歧",
    },
    "L2-WRITTEN-EXPR": {
        "name": "书面表达与文档工程", "tier": "L2", "cat": "content",
        "def": "产出结构清晰、可被他人直接使用的文档",
    },
    "L2-LEARNING": {
        "name": "快速学习与技术迁移", "tier": "L2", "cat": "process",
        "def": "在有限时间内掌握陌生领域的够用知识并投入使用",
    },
    # ── L3 跨类迁移（独占 meta 族：元能力不接受迁移折价）──────────────────
    "L3-CAP-MATRIX": {
        "name": "能力矩阵自评", "tier": "L3", "cat": "meta",
        "def": "说清自己每项能力的层级、熟练度与证据",
    },
    "L3-JOB-DECONSTRUCT": {
        "name": "岗位能力拆解", "tier": "L3", "cat": "meta",
        "def": "把一份 JD 拆成带层级与权重的能力要求清单",
    },
    "L3-EXP-REWRITE": {
        "name": "经历迁移改写", "tier": "L3", "cat": "meta",
        "def": "同一段经历，按不同行业的话语体系重写而不改事实",
    },
    "L3-PATH-PLAN": {
        "name": "跨行业路径规划", "tier": "L3", "cat": "meta",
        "def": "基于现有能力设计弯路最少的迁移路线",
    },
}

TIERS = ("L1", "L2", "L3")
TIER_LABEL = {"L1": "垂类专属", "L2": "非垂类通用", "L3": "跨类迁移"}

# ── 算分常量（自检直接断言这些值，改它们必须同步改自检）────────────────────
W_TIER = {"L1": 0.50, "L2": 0.30, "L3": 0.20}
TRANSFER_FACTOR = 0.60
LEVEL_STEPS = (1.0, 0.7, 0.4, 0.0)
W_DEFAULT = 2
LV_MAX = 4

# ── 择业场景阈值 ────────────────────────────────────────────────────────
SCENE_FIT_VERTICAL = 45     # intent=vertical 时的放行线
SCENE_A_FIT = 72            # 垂类精准
SCENE_A_L1 = 65
SCENE_B_FIT = 55            # 非垂类宽泛
SCENE_B_L2 = 60
SCENE_B_MIGRATE = 40
SCENE_C_L1 = 45             # 跨行业转型
SCENE_C_L2 = 50

SCENES = {
    "A": {"label": "垂类精准求职", "hint": "加深 L1、用深度做差异化；简历主打垂类成果"},
    "B": {"label": "非垂类宽泛择业", "hint": "扩到相邻职能；简历主打可迁移性"},
    "C": {"label": "跨行业转型", "hint": "走跳板岗位；简历主打能力等价物，弱化行业标签"},
    "D": {"label": "先补地基", "hint": "L2 未达标，不建议立即投递；先补至岗位类别最低要求"},
}


# ----------------------------------------------------------------------------
# 基础工具
# ----------------------------------------------------------------------------
def level_ratio(have, need):
    """熟练度比：need-have=0→1.0, 1→0.7, 2→0.4, >=3→0。have 超出 need 记满分。"""
    try:
        have, need = int(have), int(need)
    except (TypeError, ValueError):
        return 0.0
    d = max(0, need - have)
    return LEVEL_STEPS[min(d, 3)]


def _as_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _as_tier(v, default="L2"):
    s = str(v or "").strip().upper()
    return s if s in TIERS else default


def norm_caps(raw):
    """把任意形状的能力列表归一化成 [{id,name,tier,cat,lv,w,scope,evidence,soft}]。

    容忍：字符串项、缺 cat（按 id 查目录补）、tier 小写、lv/w 为字符串数字。
    未知 id 用 X- 前缀视为自定义能力，tier/cat 取传入值或默认 L2/process。
    """
    out = []
    for item in raw or []:
        if isinstance(item, str):
            item = {"id": item, "name": item}
        if not isinstance(item, dict):
            continue
        cid = str(item.get("id") or item.get("name") or "").strip()
        if not cid:
            continue
        known = CATALOG.get(cid, {})
        tier = _as_tier(item.get("tier"), known.get("tier", "L2"))
        cat = str(item.get("cat") or known.get("cat") or "process").strip().lower()
        lv = min(LV_MAX, max(0, _as_int(item.get("lv"), 2)))
        w = min(3, max(1, _as_int(item.get("w"), W_DEFAULT)))
        scope = item.get("scope")
        if isinstance(scope, str):
            scope = [scope]
        out.append({
            "id": cid,
            "name": str(item.get("name") or known.get("name") or cid),
            "tier": tier,
            "cat": cat,
            "lv": lv,
            "w": w,
            "scope": [str(s) for s in (scope or [])],
            "evidence": str(item.get("evidence") or "[待补充]"),
            "soft": bool(item.get("soft")),
        })
    return out


def share_bucket(caps):
    """三层占比：按熟练度加权，最大余数法凑整，保证三项和恒为 100。

    全部 lv 为 0 时退回按条数计权；无任何能力项时三层均为 0。
    """
    weight = {t: 0 for t in TIERS}
    for p in caps:
        weight[p["tier"]] += max(0, p["lv"])
    if sum(weight.values()) == 0:
        for p in caps:
            weight[p["tier"]] += 1
    total = sum(weight.values())
    if total == 0:
        return {t: 0 for t in TIERS}

    exact = {t: 100.0 * weight[t] / total for t in TIERS}
    base = {t: int(math.floor(exact[t])) for t in TIERS}
    rest = 100 - sum(base.values())
    order = sorted(TIERS, key=lambda t: (-(exact[t] - base[t]), t))
    for t in order[:rest]:
        base[t] += 1
    return base


def profile_hash(caps):
    payload = json.dumps(caps, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]


# ----------------------------------------------------------------------------
# 核心：单岗位分析
# ----------------------------------------------------------------------------
def _req_list(job):
    caps = job.get("capabilities")
    if not isinstance(caps, dict):
        return None
    merged = []
    for key in ("must", "plus"):
        for item in caps.get(key) or []:
            c = norm_caps([item])
            if c:
                merged.append(c[0])
    return merged


def analyze(profile, job, scene_override=None):
    """产出一个岗位的 matrix。job 无 capabilities 时返回 skipped 结构。"""
    reqs = _req_list(job)
    if not reqs:
        return {
            "skipped": True,
            "jobId": job.get("id"),
            "reason": "该岗位未做能力拆解（缺 capabilities.must），请按 capability-tiers.md 补全",
        }

    pcaps = norm_caps(profile.get("capabilities"))
    by_id = {p["id"]: p for p in pcaps}

    results = []
    for idx, r in enumerate(reqs):
        same = by_id.get(r["id"])
        if same is not None:
            results.append({
                "id": r["id"], "name": r["name"], "tier": r["tier"],
                "need": r["lv"], "have": same["lv"], "w": r["w"],
                "ratio": level_ratio(same["lv"], r["lv"]),
                "status": "hit", "fromId": same["id"], "fromName": same["name"],
                "idx": idx,
            })
            continue

        # 同族异层 → 迁移命中，按 TRANSFER_FACTOR 折价
        cands = [p for p in pcaps if p["cat"] == r["cat"] and p["tier"] != r["tier"]]
        if cands:
            best = max(cands, key=lambda p: (level_ratio(p["lv"], r["lv"]), -p["lv"], p["id"]))
            results.append({
                "id": r["id"], "name": r["name"], "tier": r["tier"],
                "need": r["lv"], "have": best["lv"], "w": r["w"],
                "ratio": round(level_ratio(best["lv"], r["lv"]) * TRANSFER_FACTOR, 4),
                "status": "transfer", "fromId": best["id"], "fromName": best["name"],
                "idx": idx,
            })
            continue

        results.append({
            "id": r["id"], "name": r["name"], "tier": r["tier"],
            "need": r["lv"], "have": 0, "w": r["w"],
            "ratio": 0.0, "status": "gap", "fromId": None, "fromName": None,
            "idx": idx,
        })

    # ── 分层命中率 ─────────────────────────────────────────────────────
    tiers = {}
    for t in TIERS:
        rows = [x for x in results if x["tier"] == t]
        wsum = sum(x["w"] for x in rows)
        hit = None
        if rows and wsum > 0:
            hit = int(round(100.0 * sum(x["w"] * x["ratio"] for x in rows) / wsum))
        tiers[t] = {
            "hit": hit,
            "req": len(rows),
            "ok": len([x for x in rows if x["ratio"] > 0]),
            "gap": len([x for x in rows if x["ratio"] == 0]),
            "weight": W_TIER[t],
        }

    valid = [t for t in TIERS if tiers[t]["hit"] is not None]
    if valid:
        wsum = sum(W_TIER[t] for t in valid)
        fit = int(round(sum(W_TIER[t] * tiers[t]["hit"] for t in valid) / wsum))
    else:
        fit = 0
    fit = max(0, min(100, fit))

    n = len(results)
    coverage = int(round(100.0 * len([x for x in results if x["ratio"] > 0]) / n))
    migrate = int(round(100.0 * len([x for x in results if x["status"] == "transfer"]) / n))

    # ── 场景判定 ───────────────────────────────────────────────────────
    intent = str(profile.get("intent") or "").strip().lower()
    if scene_override:
        intent = str(scene_override).strip().lower()
    h1, h2 = tiers["L1"]["hit"] or 0, tiers["L2"]["hit"] or 0
    code, reason = judge_scene(fit, h1, h2, migrate, intent)
    scene = {"code": code, "label": SCENES[code]["label"],
             "hint": SCENES[code]["hint"], "reason": reason}

    # ── 缺口（按权重降序、层升序、id 升序）─────────────────────────────
    gaps = []
    for x in results:
        if x["ratio"] > 0:
            continue
        gaps.append({
            "id": x["id"], "name": x["name"], "tier": x["tier"],
            "need": x["need"], "have": x["have"], "w": x["w"],
            "weeks": max(2, (x["need"] - x["have"]) * 3),
            "lever": ("无同族底座，需从零建立" if x["status"] == "gap"
                      else "同族有底座但熟练度不足，按迁移折价计仍未达标"),
        })
    gaps.sort(key=lambda g: (-g["w"], g["tier"], g["id"]))

    # ── 三列卡（展示就绪，render 不再过滤排序）──────────────────────────
    hit_ids = {r["id"] for r in reqs}
    columns = {}
    for t in TIERS:
        rows = [p for p in pcaps if p["tier"] == t]
        rows.sort(key=lambda p: (-p["lv"], p["id"]))
        columns[t] = [{
            "id": p["id"], "name": p["name"],
            "def": CATALOG.get(p["id"], {}).get("def", ""),
            "lv": p["lv"], "scope": p["scope"],
            "evidence": p["evidence"], "hit": p["id"] in hit_ids,
        } for p in rows]

    return {
        "jobId": job.get("id"),
        "jobTitle": job.get("title"),
        "score": fit,
        "coverage": coverage,
        "migrateRate": migrate,
        "scene": scene,
        "tiers": tiers,
        "share": share_bucket(pcaps),
        "columns": columns,
        "hit": [{"id": x["id"], "name": x["name"], "tier": x["tier"],
                 "ratio": x["ratio"]} for x in results if x["status"] == "hit"],
        "transfer": [{"from": x["fromName"], "to": x["name"], "tier": x["tier"],
                      "ratio": x["ratio"]} for x in results if x["status"] == "transfer"],
        "gap": gaps,
        "paths": build_paths(pcaps, results, tiers, code, gaps),
        "source": {"profileHash": profile_hash(pcaps),
                   "catalogVersion": CATALOG_VERSION},
    }


def judge_scene(fit, hit_l1, hit_l2, migrate, intent):
    """顺序判定，首个命中即返回。intent=switch 时把转型判定提到宽泛择业之前。

    转型（C）的门槛只看「被按哪一层评判」：L1 低而 L2 高，说明雇主实际在按通用能力
    评估你——这正是转型的定义。迁移率只作为佐证写进 reason，不作硬门槛：否则只有
    「一半以上要求靠跨层折价满足」才能算转型，这个条件几乎不可达。
    """
    if intent == "vertical" and fit >= SCENE_FIT_VERTICAL:
        return "A", f"用户明确只投本行业，且匹配度 {fit} ≥ {SCENE_FIT_VERTICAL}"

    c_ok = hit_l1 < SCENE_C_L1 and hit_l2 >= SCENE_C_L2
    if intent == "switch" and c_ok:
        return "C", (f"用户明确跨行业转型；L1 命中 {hit_l1} < {SCENE_C_L1}，"
                     f"L2 命中 {hit_l2} ≥ {SCENE_C_L2}（迁移率 {migrate}%）")

    if fit >= SCENE_A_FIT and hit_l1 >= SCENE_A_L1:
        return "A", f"匹配度 {fit} ≥ {SCENE_A_FIT}，L1 命中 {hit_l1} ≥ {SCENE_A_L1}"

    if fit >= SCENE_B_FIT and (hit_l2 >= SCENE_B_L2 or migrate >= SCENE_B_MIGRATE):
        return "B", (f"匹配度 {fit} ≥ {SCENE_B_FIT}，L2 命中 {hit_l2} 或"
                     f"迁移率 {migrate} 达到宽泛择业线")

    if c_ok:
        return "C", (f"L1 命中 {hit_l1} < {SCENE_C_L1}，L2 命中 {hit_l2} ≥ {SCENE_C_L2}："
                     f"雇主实际在按通用能力评估你（迁移率 {migrate}% 佐证）")

    return "D", f"匹配度 {fit} 与 L2 命中 {hit_l2} 均未达线，建议先补地基"


def build_paths(pcaps, results, tiers, scene, gaps):
    """迁移路径建议：最多 3 条，全部由已有数据推导，不含主观发挥。"""
    paths = []

    # 1. 同族跨层跳板：迁移命中里折价最高的那条
    trans = [x for x in results if x["status"] == "transfer"]
    if trans:
        best = max(trans, key=lambda x: (x["ratio"], -x["idx"]))
        paths.append({
            "title": "以同族能力为跳板",
            "from": best["fromName"], "to": best["name"],
            "action": (f"把「{best['fromName']}」的经验显式改写为「{best['name']}」的语言，"
                       f"在简历中并列呈现，使跨层折价从 {int(TRANSFER_FACTOR * 100)}% 收窄"),
            "weeks": 3,
        })

    # 2. 主攻层：由场景决定主打哪一层，不能与场景结论打架
    lead = {"A": "L1", "B": "L2", "C": "L2"}.get(scene)
    if lead is None:   # D：先补地基，主打层取当前命中最高的一层
        valid = [(t, tiers[t]["hit"]) for t in TIERS if tiers[t]["hit"] is not None]
        lead = max(valid, key=lambda kv: (kv[1], -TIERS.index(kv[0])))[0] if valid else "L2"
    lead_hit = tiers[lead]["hit"]
    act = {
        "A": "把 L1 的深度证据前置到摘要与首屏；L2 只保留能自证的条目，不堆砌",
        "B": "把 L2 的可交付物前置；L1 的行业标签弱化为背景，不作为卖点",
        "C": "把 L2 的可交付物前置，并把 L1 经历改写成目标行业能读懂的语言",
        "D": "先补 L2 到岗位类别最低要求，再谈主打层——此时加深 L1 的边际收益最低",
    }[scene]
    paths.append({
        "title": f"简历主打 {lead} {TIER_LABEL[lead]}",
        "from": f"{lead} 命中 {lead_hit if lead_hit is not None else '—'}",
        "to": SCENES[scene]["label"],
        "action": act, "weeks": 1,
    })

    # 3. 最小补齐：工期最短的缺口，先补它性价比最高
    if gaps:
        cheapest = min(gaps, key=lambda g: (g["weeks"], -g["w"], g["id"]))
        act = {
            "L1": "在现岗位内主动承接一次该类任务，把过程留成可量化结果",
            "L2": "三周内完成一次真实交付并留存产物（文档/看板/复盘）",
            "L3": "用 capability-tiers.md 的判定树，对这一项重做一遍自评并写出依据",
        }[cheapest["tier"]]
        paths.append({
            "title": f"最小补齐 · {cheapest['name']}",
            "from": f"现 lv{cheapest['have']}", "to": f"需 lv{cheapest['need']}",
            "action": act, "weeks": cheapest["weeks"],
        })

    return paths[:3]


# ----------------------------------------------------------------------------
# 批量与 IO
# ----------------------------------------------------------------------------
def merge_into_jobs(profile, jobs_data):
    """把每个 job 的 matrix 写回 jobs[].matrix。返回 (数据, 统计)。"""
    jobs = jobs_data.get("jobs") or []
    done = skipped = 0
    for job in jobs:
        m = analyze(profile, job)
        job["matrix"] = m
        if m.get("skipped"):
            skipped += 1
        else:
            done += 1
    return jobs_data, {"total": len(jobs), "done": done, "skipped": skipped}


def _read(path):
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"[x] 文件不存在：{p}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"[x] JSON 解析失败：{p} → {e}")


def _write(obj, path):
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    if path:
        Path(path).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


# ----------------------------------------------------------------------------
# 自检
# ----------------------------------------------------------------------------
def _p(cid, lv, **kw):
    base = {"id": cid, "lv": lv}
    base.update(kw)
    return base


def _job(requirements, jid="T-1", title="测试岗位"):
    return {"id": jid, "title": title, "capabilities": {"must": requirements}}


def selftest():
    checks = []

    def add(name, ok, info=""):
        checks.append((name, bool(ok), info))

    # 1. 确定性：同一输入连跑 5 次完全一致
    prof = {"intent": "broad", "capabilities": [
        _p("L1-TECH-BUILD", 3), _p("L2-DATA-LITERACY", 3), _p("L3-CAP-MATRIX", 2)]}
    jb = _job([{"id": "L1-TECH-BUILD", "tier": "L1", "lv": 3, "w": 3},
               {"id": "L2-DATA-LITERACY", "tier": "L2", "lv": 3, "w": 2},
               {"id": "L1-DATA-MODEL", "tier": "L1", "lv": 2, "w": 2}])
    runs = [json.dumps(analyze(prof, jb), sort_keys=True, ensure_ascii=False) for _ in range(5)]
    add("确定性：连跑 5 次结果一致", len(set(runs)) == 1, f"{len(runs)} 次")

    # 2. 空 profile 不崩溃，score 在 0..100
    m = analyze({"capabilities": []}, jb)
    add("空 profile 不崩溃且 score ∈ [0,100]",
        0 <= m["score"] <= 100 and m["share"] == {"L1": 0, "L2": 0, "L3": 0},
        f"score={m['score']} share={m['share']}")

    # 3. 极端输入：50 项全 lv4 不越界
    big = {"capabilities": [_p("L1-TECH-BUILD", 4), _p("L2-DATA-LITERACY", 4),
                            _p("L2-STAKEHOLDER", 4), _p("L3-PATH-PLAN", 4)] * 12 + [_p("L2-LEARNING", 4)]}
    mb = analyze(big, jb)
    add("极端 profile（49 项全 lv4）不越界",
        0 <= mb["score"] <= 100 and sum(mb["share"].values()) == 100,
        f"score={mb['score']} share={mb['share']}")

    # 4. 单调性：追加一项 id 相同、lv=need 的能力，fit 不下降
    weak = {"capabilities": [_p("L1-TECH-BUILD", 1), _p("L2-DATA-LITERACY", 1)]}
    strong = {"capabilities": [_p("L1-TECH-BUILD", 3), _p("L2-DATA-LITERACY", 1)]}
    add("单调性：补齐一项后 fit 不下降",
        analyze(strong, jb)["score"] >= analyze(weak, jb)["score"],
        f"{analyze(weak, jb)['score']} → {analyze(strong, jb)['score']}")

    # 5. share 三项和恒为 100（7 组固定组合）
    combos = [
        [1, 1, 1], [4, 0, 0], [0, 4, 0], [0, 0, 4], [3, 3, 3],
        [1, 2, 3], [4, 4, 1],
    ]
    ok5, detail = True, []
    for a, b, c in combos:
        caps = []
        for i in range(a):
            caps.append(_p("L1-TECH-BUILD", 4 if i == 0 else 1))
        for i in range(b):
            caps.append(_p("L2-LEARNING", 4 if i == 0 else 1))
        for i in range(c):
            caps.append(_p("L3-PATH-PLAN", 4 if i == 0 else 1))
        s = share_bucket(norm_caps(caps))
        ok5 = ok5 and sum(s.values()) == 100
        detail.append(f"{s['L1']}/{s['L2']}/{s['L3']}")
    add("share 三项和恒为 100（7 组）", ok5, " ".join(detail))

    # 6. level_ratio 单调且 have>=need 必为 1.0
    seq = [level_ratio(h, 4) for h in range(5)]
    ok6 = all(seq[i] <= seq[i + 1] + 1e-9 for i in range(4)) and level_ratio(4, 4) == 1.0 \
        and level_ratio(9, 2) == 1.0
    add("level_ratio 单调且达标即满分", ok6, "→".join(f"{v:g}" for v in seq))

    # 7. 迁移折价：同族异层落 transfer 且 ratio == 0.6
    mp = analyze({"capabilities": [_p("L1-DATA-MODEL", 3)]},
                 _job([{"id": "L2-DATA-LITERACY", "tier": "L2", "lv": 3, "w": 2}]))
    add("同族异层落 transfer 且折价 0.6",
        len(mp["transfer"]) == 1 and abs(mp["transfer"][0]["ratio"] - TRANSFER_FACTOR) < 1e-9
        and not mp["hit"],
        f"transfer={mp['transfer']}")

    # 8. 场景判定 A / B / C / D 各能触发
    sA = judge_scene(80, 70, 60, 0, "broad")[0]
    sB = judge_scene(60, 50, 65, 20, "broad")[0]
    sC = judge_scene(50, 40, 60, 50, "broad")[0]
    sD = judge_scene(30, 20, 20, 0, "broad")[0]
    sV = judge_scene(50, 20, 20, 0, "vertical")[0]
    sS = judge_scene(60, 40, 60, 50, "switch")[0]
    add("场景判定 A/B/C/D 可触发（含 vertical 与 switch 覆盖）",
        (sA, sB, sC, sD, sV, sS) == ("A", "B", "C", "D", "A", "C"),
        f"{sA}{sB}{sC}{sD} vertical={sV} switch={sS}")

    # 9. 老数据：job 无 capabilities → skipped 而非异常
    old = analyze({"capabilities": [_p("L1-TECH-BUILD", 3)]}, {"id": "old", "title": "老岗位"})
    add("老数据（无 capabilities）返回 skipped",
        old.get("skipped") is True and "reason" in old, old.get("reason", "")[:40])

    # 10. JSON 可往返、必填键齐全、gap 有序
    rt = json.loads(json.dumps(m, ensure_ascii=False))
    keys = {"jobId", "jobTitle", "score", "coverage", "migrateRate", "scene",
            "tiers", "share", "columns", "hit", "transfer", "gap", "paths", "source"}
    g = m["gap"]
    ordered = g == sorted(g, key=lambda x: (-x["w"], x["tier"], x["id"]))
    add("输出 JSON 可往返且 gap 按 (w↓, tier↑, id↑) 有序",
        keys <= set(rt) and ordered, f"缺 {sorted(keys - set(rt)) or '无'}，gap={len(g)} 条")

    # 11. 目录自洽：每项 tier 与 id 前缀一致、cat 在已知集合内
    cats = {"tech", "data", "content", "research", "business", "compliance",
            "process", "people", "meta"}
    bad = [k for k, v in CATALOG.items()
           if not k.startswith(v["tier"] + "-") or v["cat"] not in cats or not v["def"]]
    add(f"目录自洽（{len(CATALOG)} 项，tier 与 id 前缀一致）", not bad, ", ".join(bad) or "OK")

    allok = True
    print("=== capability_matrix.py 自检 ===")
    for name, ok, info in checks:
        print(f"[{'✓' if ok else '✗'}] {name}" + (f"  -> {info}" if info else ""))
        allok = allok and ok
    print("\n" + ("[✓] 全部自检通过" if allok else "[✗] 存在失败项"))
    return 0 if allok else 1


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="三级能力矩阵计算器")
    ap.add_argument("--profile", help="profile.json 路径")
    ap.add_argument("--job", help="单个 job JSON（含 capabilities）")
    ap.add_argument("--jobs", help="jobs.json（含 jobs[]）")
    ap.add_argument("--merge", action="store_true",
                    help="配合 --jobs：把 matrix 写回每个 jobs[].matrix")
    ap.add_argument("--scene", choices=["auto", "vertical", "broad", "switch"],
                    default="auto", help="覆盖 profile.intent 的场景判定")
    ap.add_argument("--out", help="输出路径；缺省写 stdout")
    ap.add_argument("--selftest", action="store_true", help="只跑自检")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if not args.profile:
        print("[x] 需要 --profile", file=sys.stderr)
        return 1
    if not (args.job or args.jobs):
        print("[x] 需要 --job 或 --jobs", file=sys.stderr)
        return 1

    profile = _read(args.profile)
    override = None if args.scene == "auto" else args.scene

    if args.jobs:
        data = _read(args.jobs)
        if not isinstance(data.get("jobs"), list):
            print("[x] --jobs 文件缺少 jobs 数组", file=sys.stderr)
            return 1
        if not args.merge:
            print("[x] 配合 --jobs 请加 --merge（否则没有输出目标）", file=sys.stderr)
            return 1
        data, stat = merge_into_jobs(profile, data)
        _write(data, args.out)
        print(f"[✓] 已写入 {stat['done']} 个岗位的能力矩阵"
              f"（跳过 {stat['skipped']} 个未做能力拆解的岗位）"
              f" → {args.out or 'stdout'}", file=sys.stderr)
        return 0

    job = _read(args.job)
    m = analyze(profile, job, override)
    _write(m, args.out)
    if not args.out:
        pass
    else:
        if m.get("skipped"):
            print(f"[!] {m['reason']}", file=sys.stderr)
        else:
            print(f"[✓] {m['jobTitle']}：匹配度 {m['score']} · "
                  f"场景 {m['scene']['code']} {m['scene']['label']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

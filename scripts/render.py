#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render.py — 求职简历蜕变引导页生成器

读 jobs.json（schema 见 references/data-contract.md），产出单文件 HTML 引导页：
  ① 岗位定锚（JD + 职位要求）  ② 定制简历 + 命中率对照表
  ③ 项目成果（P0/P1/P2）      ④ 二创来源矩阵
  ⑤ 蜕变路线（90天路线图 + 自检 + 投递策略）

零依赖（仅标准库 + 本目录 design_systems.py），内联 CSS/JS，双击即开。

## 视觉层

配色、字体、间距、圆角、投影全部由 `design_systems.py` 的 token 驱动，
每个学科轨道绑定一套真实设计系统（来自 OpenDesign 设计系统包，Apache-2.0）：

    sci 理工科   -> Vercel     近白画布 / 近黑文字 / 单一蓝强调
    art 人文社科 -> Editorial  暖纸面 / 衬线标题 / 赭石强调
    biz 经管商科 -> Stripe     白底 / 藏青文字 / 紫罗兰强调

产出 HTML 里所有颜色都通过 `var(--token)` 引用，不散落硬编码色值；
换主题 = 换一套 token，新增主题只需在 design_systems.py 登记。

用法：
  python render.py jobs.json out.html
  python render.py jobs.json out.html --title "标题" --subtitle "副标题"
  python render.py jobs.json out.html --theme art      # sci|art|biz，默认按 meta.track
  python render.py jobs.json out.html --no-repo        # 跳过第 4 步
  python render.py jobs.json out.html --no-cap         # 跳过第 6 步（强制五步版本）
  python render.py --selftest jobs.json                # 只校验数据

六步流水线：① 岗位定锚 ② 定制简历 ③ 项目成果 ④ 二创来源 ⑤ 蜕变路线 ⑥ 能力迁移矩阵。
第 6 步的数据来自 `capability_matrix.py --merge` 写入的 jobs[].matrix；
岗位没有 capabilities 时该步整段不生成，页面自动回落到五步版本（老数据兼容）。
"""

import argparse
import html
import json
import re
import sys
from datetime import date

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import design_systems  # noqa: E402  （本目录下的 token 层，非第三方包）

# ----------------------------------------------------------------------------
# 主题：文案与设计系统绑定
# ----------------------------------------------------------------------------
# 视觉（颜色/字体/间距/圆角/投影）全部来自 design_systems.py 的 token，
# 这里只保留「文案与语域」——每个轨道说什么、第 4 步叫什么。
THEMES = {
    "sci": {
        "label": "理工科",
        "step4_title": "开源项目 · 二创指引",
        "step4_sub": "点击展开每个项目的「二创切入点」。",
        "step3_sub": "P0 = 必做（简历核心证据）；P1 = 加分；P2 = 差异化亮点。",
        "step6_sub": "三层命中率按要求权重加权；跨层同族能力按 0.6 折价计入迁移。",
    },
    "art": {
        "label": "人文社科",
        "step4_title": "案例与素材 · 二创指引",
        "step4_sub": "点击展开每个案例的「二创切入点」。作品集与调研报告同样是硬证据。",
        "step3_sub": "P0 = 必做（作品集核心证据）；P1 = 加分；P2 = 差异化亮点。文科不必写代码。",
        "step6_sub": "作品集与调研报告是最容易被低估的可迁移证据——先看 L2 命中率。",
    },
    "biz": {
        "label": "经管商科",
        "step4_title": "研报与案例 · 二创指引",
        "step4_sub": "点击展开每个来源的「二创切入点」。",
        "step3_sub": "P0 = 必做（简历核心证据）；P1 = 加分；P2 = 差异化亮点。",
        "step6_sub": "商业分析属 L1，指标素养属 L2——转型时先把 L2 讲成硬贡献。",
    },
}

# ----------------------------------------------------------------------------
# 校验
# ----------------------------------------------------------------------------
P_VALUES = {"P0", "P1", "P2"}
TRACKS = set(THEMES)
# 三级能力体系：与 capability_matrix.py 的 TIERS 保持一致
TIERS = ("L1", "L2", "L3")


def selftest(path):
    """校验 jobs.json；返回 (errors, warnings)。"""
    errs, warns = [], []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return [f"文件不存在：{path}"], []
    except json.JSONDecodeError as e:
        return [f"JSON 解析失败：{e}"], []

    if not isinstance(data, dict):
        return ["顶层必须是 JSON 对象"], []

    meta = data.get("meta")
    if not isinstance(meta, dict):
        errs.append("meta 缺失或不是对象")
        meta = {}
    if not meta.get("title"):
        errs.append("meta.title 必填")
    track = meta.get("track")
    if track and track not in TRACKS:
        errs.append(f"meta.track 取值非法：{track!r}（应为 sci/art/biz）")
    if not meta.get("track"):
        warns.append("meta.track 未设置，将默认使用 sci 主题")

    jobs = data.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        errs.append("jobs 必须是非空数组")
        return errs, warns

    seen_ids = set()
    for i, j in enumerate(jobs):
        tag = f"jobs[{i}]"
        if not isinstance(j, dict):
            errs.append(f"{tag} 不是对象")
            continue
        jid = j.get("id")
        if not jid:
            errs.append(f"{tag}.id 必填")
        elif jid in seen_ids:
            errs.append(f"{tag}.id 重复：{jid}")
        else:
            seen_ids.add(jid)

        title = j.get("title")
        if not title:
            errs.append(f"{tag}.title 必填")
        if j.get("track") and j["track"] not in TRACKS:
            errs.append(f"{tag}.track 取值非法：{j['track']!r}")

        for field in ("jd", "req", "keywords"):
            v = j.get(field)
            if not isinstance(v, list) or not v:
                errs.append(f"{tag}.{field} 必须是非空数组")

        kw = j.get("keywords")
        if isinstance(kw, list) and kw and not (8 <= len(kw) <= 20):
            warns.append(f"{tag}.keywords 建议 10-15 个，当前 {len(kw)} 个")

        res = j.get("resume")
        if not isinstance(res, dict):
            errs.append(f"{tag}.resume 缺失或不是对象")
        else:
            for field in ("summary", "skills", "projects", "match"):
                if not res.get(field):
                    errs.append(f"{tag}.resume.{field} 缺失或为空")
            m = res.get("match")
            if isinstance(m, list):
                for k, pair in enumerate(m):
                    if not (isinstance(pair, list) and len(pair) == 2):
                        errs.append(f"{tag}.resume.match[{k}] 必须是 [要求, 证据] 二元组")
            sk = res.get("skills")
            if isinstance(sk, list):
                for k, s in enumerate(sk):
                    if not isinstance(s, dict) or not s.get("k"):
                        errs.append(f"{tag}.resume.skills[{k}] 必须有 k 字段")

        build = j.get("build")
        if not isinstance(build, list) or not build:
            errs.append(f"{tag}.build 必须是非空数组")
        else:
            for k, b in enumerate(build):
                if not isinstance(b, dict):
                    errs.append(f"{tag}.build[{k}] 不是对象")
                    continue
                if b.get("p") not in P_VALUES:
                    errs.append(f"{tag}.build[{k}].p 必须是 P0/P1/P2，当前 {b.get('p')!r}")
                if not b.get("t"):
                    errs.append(f"{tag}.build[{k}].t 必填")

        repos = j.get("repos") or []
        if not isinstance(repos, list):
            errs.append(f"{tag}.repos 必须是数组")
        else:
            for k, r in enumerate(repos):
                if not isinstance(r, dict):
                    errs.append(f"{tag}.repos[{k}] 不是对象")
                    continue
                if not r.get("name"):
                    errs.append(f"{tag}.repos[{k}].name 必填")
                fk = r.get("fork")
                if not isinstance(fk, list) or not fk:
                    errs.append(f"{tag}.repos[{k}].fork 必须是非空数组（要可执行的切入点）")

        # ── 第 6 步：能力要求与能力矩阵 ──────────────────────────────────
        caps = j.get("capabilities")
        if caps is not None:
            if not isinstance(caps, dict):
                errs.append(f"{tag}.capabilities 必须是对象")
            else:
                must = caps.get("must")
                if not isinstance(must, list) or not must:
                    errs.append(f"{tag}.capabilities.must 必须是非空数组"
                                f"（不打算做能力拆解就整段删掉）")
                elif not (1 <= len(must) <= 8):
                    warns.append(f"{tag}.capabilities.must 建议 1-8 项，当前 {len(must)} 项")
                for key in ("must", "plus"):
                    for k, c in enumerate(caps.get(key) or []):
                        ct = f"{tag}.capabilities.{key}[{k}]"
                        if not isinstance(c, dict):
                            errs.append(f"{ct} 不是对象")
                            continue
                        if not c.get("id"):
                            errs.append(f"{ct}.id 必填（取自 16 项目录，或 X-<slug>）")
                        if not c.get("name"):
                            errs.append(f"{ct}.name 必填")
                        if c.get("tier") not in TIERS:
                            errs.append(f"{ct}.tier 必须是 L1/L2/L3，当前 {c.get('tier')!r}")
                        if not c.get("cat"):
                            errs.append(f"{ct}.cat 必填（能力族，用于跨层迁移匹配）")
                        lv = c.get("lv")
                        if isinstance(lv, bool) or not isinstance(lv, int) or not (0 <= lv <= 4):
                            errs.append(f"{ct}.lv 必须是 0-4 整数，当前 {lv!r}")
                        w = c.get("w", 2)
                        if isinstance(w, bool) or not isinstance(w, int) or not (1 <= w <= 3):
                            errs.append(f"{ct}.w 必须是 1-3 整数，当前 {w!r}")

        mtx = j.get("matrix")
        if mtx is not None:
            if not isinstance(mtx, dict):
                errs.append(f"{tag}.matrix 必须是对象")
            elif not mtx.get("skipped"):
                for key in ("score", "coverage", "migrateRate"):
                    v = mtx.get(key)
                    if isinstance(v, bool) or not isinstance(v, int) or not (0 <= v <= 100):
                        errs.append(f"{tag}.matrix.{key} 必须是 0-100 整数，当前 {v!r}")
                sh = mtx.get("share")
                if not isinstance(sh, dict) or not set(TIERS) <= set(sh):
                    errs.append(f"{tag}.matrix.share 必须含 L1/L2/L3 三键")
                else:
                    total = sum(int(sh.get(t) or 0) for t in TIERS)
                    if total not in (0, 100):
                        errs.append(f"{tag}.matrix.share 三项之和应为 100，当前 {total}"
                                    f"（全 0 表示没有能力项）")
                if not isinstance(mtx.get("gap"), list):
                    errs.append(f"{tag}.matrix.gap 必须是数组")
                if not isinstance(mtx.get("paths"), list):
                    errs.append(f"{tag}.matrix.paths 必须是数组")
                cols = mtx.get("columns")
                if not isinstance(cols, dict) or not set(TIERS) <= set(cols):
                    errs.append(f"{tag}.matrix.columns 必须含 L1/L2/L3 三键")
                scene = mtx.get("scene")
                if not isinstance(scene, dict) or not scene.get("code"):
                    errs.append(f"{tag}.matrix.scene 缺失或没有 code")
        if caps and not mtx:
            warns.append(f"{tag} 有 capabilities 但无 matrix：第 6 步将显示占位"
                         f"（跑 capability_matrix.py --merge 生成）")
        if mtx and not caps:
            warns.append(f"{tag} 有 matrix 但无 capabilities：matrix 来源不明，建议重算")

    gl = data.get("global") or {}
    if not gl.get("roadmap"):
        warns.append("global.roadmap 为空，第 5 步将显示占位")
    if not gl.get("checklist"):
        warns.append("global.checklist 为空")
    if not gl.get("strategy"):
        warns.append("global.strategy 为空")

    return errs, warns


# ----------------------------------------------------------------------------
# 渲染辅助
# ----------------------------------------------------------------------------
def esc(s):
    """HTML 转义（防 XSS）。"""
    return html.escape(str(s if s is not None else ""), quote=True)


def hl(s):
    """
    把 [待补充：...] / [待补充] 转成红色高亮，【示例写法】转成紫色高亮。
    输入必须已经过 esc()。输出是安全 HTML。
    """
    s = str(s or "")
    s = re.sub(r"\[待补充[^\]]*\]",
               lambda m: f'<span class="placeholder">{m.group(0)}</span>', s)
    s = re.sub(r"【示例写法[^】]*】",
               lambda m: f'<span class="example">{m.group(0)}</span>', s)
    return s


def bold(s):
    """**粗体** → <b>。输入需已 esc。"""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", str(s or ""))


def json_for_script(obj):
    """
    安全地把 Python 对象序列化进 <script>。
    转义 </ 防止 `</script>` 提前闭合；转义行分隔符。
    """
    s = json.dumps(obj, ensure_ascii=False)
    return (s.replace("</", "<\\/")
             .replace("\u2028", "\\u2028")
             .replace("\u2029", "\\u2029"))


def chk_key(title, meta):
    """自检表的 localStorage key。用 sha1 而非内置 hash()：
    hash() 受 PYTHONHASHSEED 影响，同一份数据两次渲染会得到不同的 key，
    导致重渲染后旧的勾选进度全部丢失、且产出文件无法逐字节比对。"""
    import hashlib
    seed = str(meta.get("station_id") or title or "")
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]


# ----------------------------------------------------------------------------
# CSS
# ----------------------------------------------------------------------------
def _credit(ds):
    """产出 CSS 注释形式的署名块（Apache-2.0 要求的保留声明）。"""
    return (f"/* 视觉系统：{ds['name']} — {ds['voice']}\n"
            f"   token 取自 OpenDesign 设计系统包（Apache-2.0）\n"
            f"   {ds['upstream']}\n"
            f"   由 scripts/design_systems.py 预编译；要改配色/字体/间距请改该文件，\n"
            f"   不要手改下面的 :root 块（下次渲染会被覆盖）。 */")


def build_css(track):
    """产出内联 CSS。

    所有颜色 / 字体 / 间距 / 圆角 / 投影都经 var(--token) 引用，值来自
    design_systems.py；本函数只写「结构」，不写「色值」。这样换主题不会漏改。
    """
    tokens, ds = design_systems.css_root(track)
    return _CSS.replace("__CREDIT__", _credit(ds)).replace("__TOKENS__", tokens)


# CSS 用普通字符串（非 f-string），避免与 CSS 花括号冲突；占位符在 build_css 里替换。
_CSS = """
__CREDIT__

:root{
__TOKENS__
}

/* ── 基础 ────────────────────────────────────────────────────────── */
*,*::before,*::after{box-sizing:border-box}
*{margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
@media(prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
body{
  background:var(--bg);color:var(--fg);
  font-family:var(--font-body);font-size:var(--text-base);
  line-height:var(--leading-body);
  -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
}
a{color:var(--accent);text-decoration:none;text-underline-offset:.18em}
a:hover{color:var(--accent-hover);text-decoration:underline}
:focus-visible{outline:none;box-shadow:var(--focus-ring);border-radius:var(--radius-sm)}
::selection{background:var(--accent-soft);color:var(--fg)}
h1,h2,h3{font-family:var(--font-display);font-weight:700;line-height:var(--leading-tight)}
h1{font-size:clamp(27px,3.6vw,var(--text-3xl));font-weight:800;letter-spacing:var(--tracking-display)}
h2{font-size:clamp(19px,2vw,var(--text-xl));letter-spacing:-.012em}
b,strong{font-weight:700}

/* ── 头部：平涂表面，不做渐变光晕 ─────────────────────────────────── */
.hero{
  background:var(--surface);border-bottom:1px solid var(--border);
  padding:calc(var(--space-12) + var(--space-6)) var(--container-gutter-desktop) var(--space-12);
}
.hero-inner{max-width:var(--container-max);margin:0 auto}
.badge{
  display:inline-flex;align-items:center;gap:var(--space-2);
  padding:var(--space-1) var(--space-3);margin-bottom:var(--space-5);
  border:1px solid var(--border);border-radius:var(--radius-pill);
  background:var(--surface-2);color:var(--fg-2);
  font-size:var(--text-xs);font-weight:600;letter-spacing:.02em;
}
.badge .dot{width:6px;height:6px;border-radius:50%;background:var(--success);flex:none}
.hero h1{max-width:24ch;margin-bottom:var(--space-4)}
.hero p.sub{color:var(--muted);font-size:var(--text-lg);max-width:68ch;line-height:1.55}
.hero-stats{display:flex;flex-wrap:wrap;gap:var(--space-3);margin-top:var(--space-8)}
.stat{
  background:var(--surface-2);border:1px solid var(--border);
  border-radius:var(--radius-md);padding:var(--space-3) var(--space-5);min-width:112px;
}
.stat .n{
  font-family:var(--font-display);font-size:var(--text-xl);font-weight:700;
  color:var(--fg);line-height:1.15;font-variant-numeric:tabular-nums;
}
.stat .l{font-size:var(--text-xs);color:var(--muted);font-weight:500;margin-top:2px}

/* ── 吸顶导航：hairline + 激活态用下划线，不用填充药丸 ───────────── */
.navbar{
  position:sticky;top:0;z-index:50;
  background:var(--surface-translucent);
  -webkit-backdrop-filter:saturate(1.6) blur(14px);
  backdrop-filter:saturate(1.6) blur(14px);
  border-bottom:1px solid var(--border);
}
.nav-inner{
  max-width:var(--container-max);margin:0 auto;
  padding:var(--space-3) var(--container-gutter-desktop);
  display:flex;align-items:center;gap:var(--space-1);flex-wrap:wrap;
}
.brandmark{
  font-family:var(--font-display);font-weight:700;font-size:var(--text-sm);
  color:var(--fg);margin-right:var(--space-4);white-space:nowrap;letter-spacing:-.01em;
}
.brandmark span{color:var(--accent);font-weight:400}
.navlink{
  position:relative;font-size:var(--text-sm);font-weight:500;color:var(--muted);
  padding:var(--space-2) var(--space-3);border-radius:var(--radius-sm);white-space:nowrap;
  transition:color var(--motion-fast) var(--ease-standard),background var(--motion-fast) var(--ease-standard);
}
.navlink:hover{color:var(--fg);background:var(--surface-2);text-decoration:none}
.navlink.active{color:var(--accent);font-weight:600;background:transparent}
.navlink.active::after{
  content:"";position:absolute;left:var(--space-3);right:var(--space-3);bottom:1px;
  height:2px;background:var(--accent);border-radius:1px;
}

/* ── 版心与章节节奏 ──────────────────────────────────────────────── */
.wrap{max-width:var(--container-max);margin:0 auto;padding:0 var(--container-gutter-desktop)}
section.block{padding:var(--section-y-desktop) 0 0}
.sec-head{display:flex;align-items:flex-start;gap:var(--space-4);margin-bottom:var(--space-8)}
.sec-num{
  flex:none;width:34px;height:34px;border-radius:var(--radius-sm);
  display:grid;place-items:center;
  border:1px solid var(--border);background:var(--surface-2);
  color:var(--accent);font-family:var(--font-mono);font-weight:600;font-size:var(--text-sm);
}
.sec-head h2{margin-bottom:var(--space-2)}
.sec-head p{color:var(--muted);font-size:var(--text-sm);max-width:76ch}

/* ── 岗位切换器 ──────────────────────────────────────────────────── */
.tabs{
  display:flex;gap:var(--space-2);overflow-x:auto;
  padding-bottom:var(--space-2);margin-bottom:var(--space-6);scrollbar-width:thin;
}
.tab{
  flex:none;padding:var(--space-2) var(--space-4);
  border:1px solid var(--border);border-radius:var(--radius-pill);
  background:var(--surface);color:var(--fg-2);
  font-size:var(--text-sm);font-weight:500;cursor:pointer;white-space:nowrap;
  transition:color var(--motion-fast) var(--ease-standard),background var(--motion-fast) var(--ease-standard),border-color var(--motion-fast) var(--ease-standard);
}
.tab:hover{border-color:var(--accent);color:var(--accent)}
.tab.active{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.tab .ti{font-family:var(--font-mono);font-size:var(--text-xs);opacity:.55;margin-right:var(--space-2)}
.job-meta{
  display:flex;flex-wrap:wrap;gap:var(--space-2);align-items:center;
  margin-bottom:var(--space-8);padding:var(--space-4) var(--space-5);
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-md);
}
.job-meta .t{font-family:var(--font-display);font-size:var(--text-lg);font-weight:700;letter-spacing:-.01em}
.chip{
  font-size:var(--text-xs);font-weight:600;padding:3px var(--space-3);
  border-radius:var(--radius-pill);background:var(--accent-soft);color:var(--accent-ink);
}
.chip.gray{background:var(--surface-2);color:var(--fg-2)}
.chip.warn{background:var(--warn-soft);color:var(--warn-ink)}
.chip.link{background:var(--success-soft);color:var(--success-ink)}

/* ── 卡片：hairline 边框，不做无意义投影 ─────────────────────────── */
.card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius-lg);margin-bottom:var(--space-5);overflow:hidden;
}
.card-h{
  padding:var(--space-4) var(--space-5);border-bottom:1px solid var(--border-soft);
  display:flex;align-items:center;gap:var(--space-3);
  font-family:var(--font-display);font-weight:700;font-size:var(--text-sm);letter-spacing:-.005em;
}
.card-h .ic{
  width:24px;height:24px;border-radius:var(--radius-sm);
  display:grid;place-items:center;font-size:var(--text-xs);flex:none;font-weight:600;
}
.card-h .ic.blue{background:var(--accent-soft);color:var(--accent-ink)}
.card-h .ic.green{background:var(--success-soft);color:var(--success-ink)}
.card-h .ic.orange{background:var(--warn-soft);color:var(--warn-ink)}
.card-h .ic.purple{background:var(--p2-soft);color:var(--p2-ink)}
.card-b{padding:var(--space-5)}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-5)}
@media(max-width:880px){.two-col{grid-template-columns:1fr}}

/* ── JD / 要求条目 ───────────────────────────────────────────────── */
.jd-item,.req-item{
  position:relative;padding-left:var(--space-5);margin-bottom:var(--space-3);
  font-size:var(--text-sm);color:var(--fg-2);
}
.jd-item::before,.req-item::before{
  content:"";position:absolute;left:2px;top:.62em;width:5px;height:5px;border-radius:50%;
}
.jd-item::before{background:var(--accent)}
.req-item::before{background:var(--success)}
.req-item.plus::before{background:var(--warn)}
.jd-item:last-child,.req-item:last-child{margin-bottom:0}

/* ── 关键词 ──────────────────────────────────────────────────────── */
.kw-wrap{
  display:flex;flex-wrap:wrap;gap:var(--space-2);
  padding:var(--space-4) var(--space-5);background:var(--surface-2);
}
.kw{
  font-size:var(--text-xs);font-weight:600;padding:var(--space-1) var(--space-3);
  border-radius:var(--radius-sm);background:var(--surface);border:1px solid var(--border);color:var(--fg-2);
}
.kw-label{font-size:var(--text-xs);font-weight:700;color:var(--muted);align-self:center;margin-right:var(--space-1)}

/* ── 简历 ────────────────────────────────────────────────────────── */
.resume{font-size:var(--text-sm)}
.resume .rname{font-family:var(--font-display);font-size:var(--text-lg);font-weight:700;letter-spacing:-.01em}
.resume .rname .rcontact{font-weight:500;color:var(--muted);font-size:var(--text-xs)}
.resume .rpos{font-size:var(--text-sm);color:var(--accent);font-weight:600;margin-top:var(--space-1)}
.resume .rnote{font-size:var(--text-sm);color:var(--accent);font-weight:600;margin-top:var(--space-2)}
.resume .rsum{
  margin-top:var(--space-4);padding:var(--space-4);
  background:var(--surface-2);border-left:2px solid var(--accent);
  border-radius:0 var(--radius-sm) var(--radius-sm) 0;color:var(--fg-2);
}
.rsec{margin-top:var(--space-5)}
.rsec-t{
  font-size:var(--text-xs);font-weight:700;letter-spacing:.08em;color:var(--muted);
  text-transform:uppercase;margin-bottom:var(--space-3);display:flex;align-items:center;gap:var(--space-3);
}
.rsec-t::after{content:"";flex:1;height:1px;background:var(--border-soft)}
.skill-row{display:flex;gap:var(--space-3);margin-bottom:var(--space-2);font-size:var(--text-sm)}
.skill-row .sk{flex:none;width:118px;font-weight:600;color:var(--fg)}
.skill-row .sv{color:var(--fg-2)}
.hitmark{
  background:var(--mark-bg);border-bottom:2px solid var(--mark-line);
  font-weight:600;border-radius:2px;padding:0 2px;
}
.proj{
  border:1px solid var(--border);border-radius:var(--radius-md);
  padding:var(--space-4);margin-bottom:var(--space-3);background:var(--surface);
}
.proj .pn{font-weight:700;font-size:var(--text-sm);color:var(--fg)}
.proj .ps{
  font-family:var(--font-mono);font-size:var(--text-xs);color:var(--accent);
  font-weight:600;margin:var(--space-1) 0 var(--space-2);
}
.proj .pb{font-size:var(--text-sm);color:var(--fg-2);white-space:pre-line}
.placeholder{
  color:var(--danger);font-weight:700;background:var(--danger-soft);
  padding:0 3px;border-radius:3px;font-size:.92em;
}
.example{
  color:var(--p2-ink);font-weight:700;background:var(--p2-soft);
  padding:0 3px;border-radius:3px;font-size:.92em;
}

/* ── 表格 ────────────────────────────────────────────────────────── */
table{width:100%;border-collapse:collapse;font-size:var(--text-sm)}
th,td{text-align:left;padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--border-soft);vertical-align:top}
th{
  background:var(--surface-2);font-weight:600;color:var(--muted);
  font-size:var(--text-xs);letter-spacing:.04em;text-transform:uppercase;
}
tbody tr:hover{background:var(--surface-2)}
tr:last-child td{border-bottom:none}
td.ev{color:var(--fg-2)}

/* ── P0/P1/P2 项目卡 ─────────────────────────────────────────────── */
.bcard{
  display:flex;gap:var(--space-3);padding:var(--space-4);
  border:1px solid var(--border);border-radius:var(--radius-md);
  margin-bottom:var(--space-3);background:var(--surface);
}
.bcard .pb-badge{
  flex:none;align-self:flex-start;font-family:var(--font-mono);
  font-size:var(--text-xs);font-weight:700;padding:2px var(--space-2);
  border-radius:var(--radius-sm);letter-spacing:.02em;
}
.pb-P0{background:var(--p0-soft);color:var(--p0-ink)}
.pb-P1{background:var(--p1-soft);color:var(--p1-ink)}
.pb-P2{background:var(--p2-soft);color:var(--p2-ink)}
.bcard .bt{font-weight:600;font-size:var(--text-sm);color:var(--fg)}
.bcard .bd{font-size:var(--text-sm);color:var(--fg-2);margin-top:var(--space-1)}

/* ── 二创来源（可展开） ──────────────────────────────────────────── */
.repo{
  border:1px solid var(--border);border-radius:var(--radius-md);
  margin-bottom:var(--space-3);overflow:hidden;background:var(--surface);
}
.repo-h{
  padding:var(--space-4) var(--space-5);display:flex;align-items:flex-start;
  gap:var(--space-3);cursor:pointer;user-select:none;
  transition:background var(--motion-fast) var(--ease-standard);
}
.repo-h:hover{background:var(--surface-2)}
.repo-h .rn{font-family:var(--font-mono);font-weight:600;font-size:var(--text-sm);color:var(--fg)}
.repo-h .rmeta{display:flex;flex-wrap:wrap;gap:var(--space-2);margin-top:var(--space-2);align-items:center}
.starchip,.langchip,.tagchip,.modechip{
  font-size:var(--text-xs);font-weight:600;padding:2px var(--space-2);border-radius:var(--radius-sm);
}
.starchip{background:var(--warn-soft);color:var(--warn-ink)}
.langchip{background:var(--accent-soft);color:var(--accent-ink)}
.tagchip{background:var(--surface-2);color:var(--fg-2)}
.modechip{background:var(--p2-soft);color:var(--p2-ink)}
.repo-h .chev{
  margin-left:auto;color:var(--muted);font-size:var(--text-xs);flex:none;margin-top:var(--space-1);
  transition:transform var(--motion-base) var(--ease-standard);
}
.repo.open .chev{transform:rotate(90deg)}
.repo-b{display:none;padding:0 var(--space-5) var(--space-5);border-top:1px solid var(--border-soft);background:var(--surface-2)}
.repo.open .repo-b{display:block}
.repo-b .why{font-size:var(--text-sm);color:var(--fg-2);margin:var(--space-4) 0 var(--space-3)}
.repo-b .fork-t{
  font-size:var(--text-xs);font-weight:700;color:var(--muted);
  letter-spacing:.06em;text-transform:uppercase;margin-bottom:var(--space-2);
}
.fork-item{position:relative;padding-left:var(--space-4);font-size:var(--text-sm);color:var(--fg-2);margin-bottom:var(--space-2)}
.fork-item::before{content:"→";position:absolute;left:0;color:var(--accent);font-weight:600}
.accept{
  margin-top:var(--space-3);padding:var(--space-3) var(--space-4);border-radius:var(--radius-sm);
  background:var(--success-soft);border:1px solid var(--border-soft);
  font-size:var(--text-sm);color:var(--success-ink);
}

/* ── 时间轴：实线 + 圆点，不用渐变线 ─────────────────────────────── */
.timeline{position:relative;padding-left:var(--space-6)}
.timeline::before{
  content:"";position:absolute;left:4px;top:8px;bottom:8px;width:1px;background:var(--border);
}
.tl-item{position:relative;margin-bottom:var(--space-6)}
.tl-item::before{
  content:"";position:absolute;left:calc(-1 * var(--space-6));top:6px;
  width:9px;height:9px;border-radius:50%;background:var(--bg);border:2px solid var(--accent);
}
.tl-item .ph{font-family:var(--font-mono);font-size:var(--text-xs);font-weight:600;color:var(--accent);letter-spacing:.02em}
.tl-item .tt{
  font-family:var(--font-display);font-size:var(--text-lg);font-weight:700;
  margin:var(--space-1) 0 var(--space-3);letter-spacing:-.01em;
}
.tl-item ul{list-style:none}
.tl-item li{position:relative;padding-left:var(--space-4);font-size:var(--text-sm);color:var(--fg-2);margin-bottom:var(--space-2)}
.tl-item li::before{content:"";position:absolute;left:2px;top:.6em;width:4px;height:4px;border-radius:50%;background:var(--muted)}

/* ── 自检勾选 ────────────────────────────────────────────────────── */
.chk{
  display:flex;gap:var(--space-3);align-items:flex-start;
  padding:var(--space-3) var(--space-4);border:1px solid var(--border);
  border-radius:var(--radius-md);margin-bottom:var(--space-2);background:var(--surface);
  cursor:pointer;font-size:var(--text-sm);color:var(--fg-2);
  transition:background var(--motion-fast) var(--ease-standard),border-color var(--motion-fast) var(--ease-standard);
}
.chk:hover{border-color:var(--accent);background:var(--surface-2)}
.chk.on{background:var(--success-soft);border-color:var(--success)}
.chk .box{
  flex:none;width:18px;height:18px;border-radius:var(--radius-sm);
  border:1px solid var(--border);background:var(--surface);
  display:grid;place-items:center;font-size:11px;color:var(--surface);
  margin-top:2px;transition:background var(--motion-fast) var(--ease-standard),color var(--motion-fast) var(--ease-standard);
}
.chk.on .box{background:var(--success);border-color:var(--success);color:var(--surface)}

/* ── 策略卡 ──────────────────────────────────────────────────────── */
.scard{
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-md);
  padding:var(--space-4);margin-bottom:var(--space-3);
}
.scard .st{
  font-weight:600;font-size:var(--text-sm);color:var(--fg);
  margin-bottom:var(--space-2);display:flex;align-items:center;gap:var(--space-2);
}
.scard .st::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--accent);flex:none}
.scard .sd{font-size:var(--text-sm);color:var(--fg-2)}

/* ── 提示条 ──────────────────────────────────────────────────────── */
.notice{
  display:flex;gap:var(--space-3);padding:var(--space-4) var(--space-5);
  border-radius:var(--radius-md);background:var(--warn-soft);border:1px solid var(--border-soft);
  font-size:var(--text-sm);color:var(--warn-ink);margin-top:var(--space-4);
}
.notice .ni{font-size:var(--text-lg);flex:none;line-height:1}
.notice b{color:var(--warn-ink);font-weight:700}
.notice.info{background:var(--accent-soft);color:var(--accent-ink)}
.notice.info b{color:var(--accent-ink)}

/* ── 第 6 步：能力迁移矩阵（L1/L2/L3 同色相明度阶梯）────────────── */
.cap-bar{
  display:flex;height:10px;border-radius:var(--radius-sm);
  overflow:hidden;background:var(--cap-rail);
}
.cap-seg{height:100%}
.cap-seg.l1{background:var(--cap-l1)}
.cap-seg.l2{background:var(--cap-l2)}
.cap-seg.l3{background:var(--cap-l3)}
.cap-legend{
  display:flex;flex-wrap:wrap;gap:var(--space-2) var(--space-5);
  margin-top:var(--space-3);font-size:var(--text-xs);color:var(--fg-2);
}
.cap-key{display:flex;align-items:center;gap:var(--space-2)}
.cap-key::before{
  content:"";width:8px;height:8px;border-radius:2px;flex:none;background:var(--cap-rail);
}
.cap-key.l1::before{background:var(--cap-l1)}
.cap-key.l2::before{background:var(--cap-l2)}
.cap-key.l3::before{background:var(--cap-l3)}
.cap-key b{color:var(--fg);font-weight:600}
.cap-key .ch{color:var(--meta);font-variant-numeric:tabular-nums}

.cap-verdict{
  display:flex;flex-wrap:wrap;gap:var(--space-1) var(--space-4);align-items:baseline;
  margin-top:var(--space-4);padding:var(--space-4) var(--space-5);
  border:1px solid var(--border-soft);border-left:3px solid var(--accent);
  border-radius:var(--radius-md);background:var(--accent-soft);
}
.cap-verdict .cv-code{
  font-family:var(--font-mono);font-size:var(--text-xs);font-weight:700;
  color:var(--accent-ink);letter-spacing:.06em;
}
.cap-verdict .cv-label{font-size:var(--text-base);font-weight:700;color:var(--fg)}
.cap-verdict .cv-stat{
  font-size:var(--text-xs);color:var(--meta);font-variant-numeric:tabular-nums;
}
.cap-verdict .cv-hint{font-size:var(--text-sm);color:var(--fg-2);flex-basis:100%}
.cap-verdict .cv-reason{font-size:var(--text-xs);color:var(--meta);flex-basis:100%}

.cap-grid{
  display:grid;grid-template-columns:repeat(3,1fr);
  gap:var(--space-4);margin-top:var(--space-4);align-items:stretch;
}
/* 列即面板：三列能力项数量天然不等（多数人 L2 最多），
   用面板底色承接短列下方的留白，读作「这一层的容器」而不是「页面没写完」。
   用 fg-soft 而不是 surface-2：后者在 Editorial 是沙色，三个大色块会压过内容。 */
.cap-col{
  display:flex;flex-direction:column;gap:var(--space-1);min-width:0;
  background:var(--fg-soft);border:1px solid var(--border);
  border-radius:var(--radius-md);padding:var(--space-3) var(--space-4) var(--space-4);
}
.cap-col-h{
  display:flex;align-items:baseline;gap:var(--space-2);
  font-size:var(--text-xs);letter-spacing:.06em;color:var(--muted);
  padding-bottom:var(--space-2);margin-bottom:var(--space-2);
  border-bottom:1px solid var(--border-soft);
}
.cap-col-h .cl{
  font-family:var(--font-mono);font-weight:700;color:var(--cap-l1-ink);
  padding-left:var(--space-2);border-left:2px solid var(--cap-l1);
}
.cap-col.c2 .cap-col-h .cl{color:var(--cap-l2-ink);border-left-color:var(--cap-l2)}
.cap-col.c3 .cap-col-h .cl{color:var(--cap-l3-ink);border-left-color:var(--cap-l3)}
.cap-col-h .cn{margin-left:auto;font-variant-numeric:tabular-nums}

/* 卡片不再自带底色与四边框：面板已经是一层容器，再加一层就是卡片套卡片 */
.cap-card{
  border:0;border-left:2px solid var(--cap-l1);
  padding:var(--space-2) 0 var(--space-2) var(--space-3);
  background:transparent;
}
.cap-col.c2 .cap-card{border-left-color:var(--cap-l2)}
.cap-col.c3 .cap-card{border-left-color:var(--cap-l3)}
.cap-card .ct{
  display:flex;align-items:baseline;gap:var(--space-2);
  font-size:var(--text-sm);font-weight:600;color:var(--fg);
}
.cap-card .ct .hit{
  font-size:10px;font-weight:700;letter-spacing:.04em;flex:none;
  padding:1px 5px;border-radius:var(--radius-sm);
  background:var(--success-soft);color:var(--success-ink);
}
.cap-card .cd{font-size:var(--text-xs);color:var(--fg-2);margin-top:var(--space-1);line-height:1.5}
.cap-card .cf{display:flex;align-items:center;gap:var(--space-2);margin-top:var(--space-2);flex-wrap:wrap}
.lv-dots{display:flex;gap:3px;flex:none}
.lv-dot{width:8px;height:8px;border-radius:2px;background:var(--border)}
.lv-dot.on{background:var(--cap-l1)}
.cap-col.c2 .lv-dot.on{background:var(--cap-l2)}
.cap-col.c3 .lv-dot.on{background:var(--cap-l3)}
.cap-scope{
  font-size:10px;padding:1px 6px;border-radius:var(--radius-sm);
  background:var(--surface);color:var(--fg-2);border:1px solid var(--border-soft);
}
.cap-ev{
  font-size:var(--text-xs);color:var(--meta);margin-top:var(--space-2);line-height:1.5;
}
.cap-empty{font-size:var(--text-xs);color:var(--meta);padding:var(--space-3) 0}

.gap-item{
  display:flex;align-items:center;gap:var(--space-3);
  padding:var(--space-3) 0;border-bottom:1px solid var(--border-soft);
  font-size:var(--text-sm);color:var(--fg-2);
}
.gap-item:last-child{border-bottom:0}
.gap-tag{
  flex:none;font-family:var(--font-mono);font-size:10px;font-weight:700;
  padding:1px 6px;border-radius:var(--radius-sm);
  background:var(--cap-l1-soft);color:var(--cap-l1-ink);
}
.gap-tag.t2{background:var(--cap-l2-soft);color:var(--cap-l2-ink)}
.gap-tag.t3{background:var(--cap-l3-soft);color:var(--cap-l3-ink)}
.gap-item .gn{color:var(--fg);font-weight:600;flex:1;min-width:0}
.gap-item .gw{
  flex:none;font-size:var(--text-xs);color:var(--meta);
  font-variant-numeric:tabular-nums;
}

.path-item{padding:var(--space-3) 0;border-bottom:1px solid var(--border-soft)}
.path-item:last-child{border-bottom:0}
.path-item .pt{
  display:flex;align-items:center;gap:var(--space-2);
  font-size:var(--text-sm);font-weight:600;color:var(--fg);
}
.path-item .pt::before{content:"→";color:var(--accent);font-weight:700;flex:none}
.path-item .pj{
  font-size:var(--text-xs);color:var(--meta);margin-top:var(--space-1);
  font-variant-numeric:tabular-nums;
}
.path-item .pa{font-size:var(--text-xs);color:var(--fg-2);margin-top:var(--space-1);line-height:1.55}
.cap-note{font-size:var(--text-xs);color:var(--accent-ink)}

/* ── 页脚 / 复制 / 吐司 ──────────────────────────────────────────── */
footer{
  padding:var(--space-12) var(--container-gutter-desktop);
  border-top:1px solid var(--border);margin-top:var(--section-y-desktop);
  text-align:center;color:var(--muted);font-size:var(--text-xs);background:var(--surface);
}
.copybtn{
  font-size:var(--text-xs);font-weight:600;color:var(--fg-2);
  background:var(--surface-2);border:1px solid var(--border);
  padding:var(--space-1) var(--space-3);border-radius:var(--radius-sm);
  cursor:pointer;margin-left:auto;
  transition:color var(--motion-fast) var(--ease-standard),border-color var(--motion-fast) var(--ease-standard);
}
.copybtn:hover{color:var(--fg);border-color:var(--fg-2)}
.copied-toast{
  position:fixed;bottom:var(--space-8);left:50%;
  transform:translateX(-50%) translateY(80px);
  background:var(--fg);color:var(--bg);padding:var(--space-3) var(--space-6);
  border-radius:var(--radius-pill);font-size:var(--text-sm);font-weight:600;
  box-shadow:var(--elev-raised);opacity:0;z-index:99;pointer-events:none;
  transition:opacity var(--motion-base) var(--ease-standard),transform var(--motion-base) var(--ease-standard);
}
.copied-toast.show{opacity:1;transform:translateX(-50%) translateY(0)}

/* ── 响应式：靠 token 重绑，不重写组件 ───────────────────────────── */
@media(max-width:900px){
  :root{
    --section-y-desktop:var(--section-y-tablet);
    --container-gutter-desktop:var(--container-gutter-tablet);
  }
  .cap-grid{grid-template-columns:1fr}
}
@media(max-width:640px){
  :root{
    --section-y-desktop:var(--section-y-phone);
    --container-gutter-desktop:var(--container-gutter-phone);
  }
  .nav-inner .brandmark{width:100%;margin-bottom:var(--space-1)}
  .hero h1{max-width:none}
}

/* ── 无障碍：尊重减少动效偏好 ───────────────────────────────────── */
@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{
    animation-duration:.01ms !important;animation-iteration-count:1 !important;
    transition-duration:.01ms !important;scroll-behavior:auto !important;
  }
}

/* ── 打印：给「打印出来看/给导师看」留一条干净路径 ───────────────── */
@media print{
  .navbar,.copybtn,.copied-toast{display:none !important}
  body{background:#fff;color:#000;font-size:10.5pt;line-height:1.5}
  .hero{border-bottom:1px solid #ccc;padding:0 0 10pt}
  .hero-stats,.stat{background:#fff;border-color:#ddd}
  .card,.repo,.bcard,.proj,.scard,.chk,.job-meta{border-color:#ddd;box-shadow:none;background:#fff}
  .kw-wrap,.repo-b,.resume .rsum,th,tbody tr:hover{background:#fff}
  section.block{padding:14pt 0 0;break-inside:avoid}
  .repo-b{display:block !important}
  .timeline::before{background:#ccc}
  a{color:#000;text-decoration:none}
  .chip,.kw,.starchip,.langchip,.tagchip,.modechip,.pb-badge{border:1px solid #ddd}
  /* 第 6 步：占比条是「数据编码」而非装饰，黑白打印丢色会让它变成空轨 */
  .cap-card,.cap-col,.cap-verdict,.gap-item,.path-item{border-color:#ddd;background:#fff}
  .cap-col{background:#fff;border:1px solid #ddd}
  .cap-bar{border:1px solid #ccc}
  .cap-seg{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .lv-dot{background:#fff;border:1px solid #999}
  .lv-dot.on{background:#666;border-color:#666;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .cap-scope,.gap-tag,.cap-card .ct .hit{border:1px solid #ddd}
}
"""




# ----------------------------------------------------------------------------
# HTML 组装
# ----------------------------------------------------------------------------
def build_html(data, theme_name, title, subtitle, no_repo, no_cap=False):
    t = THEMES[theme_name]
    meta = data.get("meta") or {}
    jobs = data.get("jobs") or []
    gl = data.get("global") or {}

    # 第 6 步只在「至少一个岗位做了能力拆解」时生成。
    # 老数据（v1.1 及更早）没有 capabilities，此处自动降级为五步页面，不报错。
    has_caps = (not no_cap) and any(
        isinstance(j.get("capabilities"), dict)
        and (j["capabilities"].get("must") or j["capabilities"].get("plus"))
        for j in jobs
    )

    title = title or meta.get("title") or "简历蜕变引导"
    subtitle = subtitle or meta.get("subtitle") or ""
    stats = data.get("stats") or []
    if not stats:
        stats = [
            {"n": str(len(jobs)), "l": "目标岗位"},
            {"n": "6" if has_caps else "5", "l": "蜕变步骤"},
        ]

    steps = [("step1", "① 岗位定锚")]
    if not no_repo:
        steps += [("step2", "② 定制简历"), ("step3", "③ 项目成果"), ("step4", "④ 二创指引")]
    else:
        steps += [("step2", "② 定制简历"), ("step3", "③ 项目成果")]
    steps.append(("step5", "⑤ 蜕变路线"))
    if has_caps:
        steps.append(("step6", "⑥ 能力迁移"))

    nav = "".join(f'<a class="navlink" href="#{i}">{esc(l)}</a>' for i, l in steps)

    stat_html = "".join(
        f'<div class="stat"><div class="n">{esc(s.get("n",""))}</div>'
        f'<div class="l">{esc(s.get("l",""))}</div></div>' for s in stats)

    source_note = meta.get("linkLabel") or ""

    repo_footer = ("" if no_repo else
                   '<div class="notice"><span class="ni">§</span><div><b>合规二创：</b>'
                   '请遵守原仓库 License、注明 fork 来源与你的增量。'
                   '简历写法示例：「基于 xxx（附链接）二次开发，实现 yyy，性能提升 z%」。</div></div>')

    subs = [f'{esc(data["meta"].get("company",""))} {esc(t["label"])} 岗位'
            if data.get("meta", {}).get("company") else esc(t["label"])]
    step_word = "六步法" if has_caps else "五步法"
    switch_sub = ("切换岗位后，下面各步（JD / 简历 / 项目 / 二创 / 能力）的内容会联动更新。"
                  if has_caps else
                  "切换岗位后，下面各步（JD / 简历 / 项目 / 二创）的内容会联动更新。")
    kw_note = ("<span class=\"placeholder\">[待补充]</span> 是<b>你必须自己填回的真实信息</b>，"
               "<span class=\"example\">【示例写法】</span> 只是表达范式，<b>请勿照抄内容</b>。")

    body = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<style>{build_css(theme_name)}</style>
</head>
<body>

<header class="hero">
  <div class="hero-inner">
    <div class="badge"><span class="dot"></span> {esc(t['label'])} · 岗位匹配已检索</div>
    <h1>{esc(title)}</h1>
    <p class="sub">{esc(subtitle)}</p>
    <div class="hero-stats">{stat_html}</div>
  </div>
</header>

<nav class="navbar">
  <div class="nav-inner">
    <div class="brandmark">{esc(meta.get('brandmark') or '简历蜕变')} <span>×</span> {step_word}</div>
    {nav}
  </div>
</nav>

<div class="wrap">

  <section class="block" id="switcher">
    <div class="sec-head">
      <div class="sec-num">◎</div>
      <div>
        <h2>选择你要主攻的岗位</h2>
        <p>{switch_sub}</p>
      </div>
    </div>
    <div class="tabs" id="jobTabs"></div>
    <div class="job-meta" id="jobMeta"></div>
  </section>

  <section class="block" id="step1">
    <div class="sec-head">
      <div class="sec-num">1</div>
      <div><h2>岗位定锚 · 职位描述与职位要求</h2>
      <p>先看清 HR 要什么。以下为检索到的原文，未作改写。</p></div>
    </div>
    <div class="two-col">
      <div class="card">
        <div class="card-h"><span class="ic blue">描</span>职位描述</div>
        <div class="card-b" id="jdBox"></div>
      </div>
      <div class="card">
        <div class="card-h"><span class="ic green">求</span>职位要求</div>
        <div class="card-b" id="reqBox"></div>
      </div>
    </div>
    <div class="card" style="margin-top:0">
      <div class="kw-wrap" id="kwBox"></div>
    </div>
    <div class="notice info"><span class="ni">ⓘ</span><div>{kw_note}</div></div>
  </section>

  <section class="block" id="step2">
    <div class="sec-head">
      <div class="sec-num">2</div>
      <div><h2>定制简历 · 针对该岗位的 HR 筛选逻辑</h2>
      <p>{kw_note}</p></div>
    </div>
    <div class="card">
      <div class="card-h"><span class="ic purple">历</span>定制简历（针对该岗位强化）<button class="copybtn" id="copyResume">复制此版本</button></div>
      <div class="card-b resume" id="resumeBox"></div>
    </div>
    <div class="card">
      <div class="card-h"><span class="ic blue">✓</span>命中率对照表 · JD 要求 → 你的证据</div>
      <div class="card-b" style="padding:0"><table id="matchTable"></table></div>
    </div>
  </section>

  <section class="block" id="step3">
    <div class="sec-head">
      <div class="sec-num">3</div>
      <div><h2>项目 · Demo · 成果推荐</h2>
      <p>{esc(t['step3_sub'])}</p></div>
    </div>
    <div id="buildBox"></div>
  </section>
"""

    if not no_repo:
        body += f"""
  <section class="block" id="step4">
    <div class="sec-head">
      <div class="sec-num">4</div>
      <div><h2>{esc(t['step4_title'])}</h2>
      <p>{esc(t['step4_sub'])}</p></div>
    </div>
    <div id="repoBox"></div>
    {repo_footer}
  </section>
"""

    body += f"""
  <section class="block" id="step5">
    <div class="sec-head">
      <div class="sec-num">5</div>
      <div><h2>蜕变路线 · 执行 + 自检 + 投递策略</h2>
      <p>把上面几步落到时间表上，勾选进度会自动保存。</p></div>
    </div>
    <div class="card">
      <div class="card-h"><span class="ic blue">图</span>执行路线图</div>
      <div class="card-b"><div class="timeline" id="roadmapBox"></div></div>
    </div>
    <div class="two-col">
      <div class="card">
        <div class="card-h"><span class="ic green">检</span>自检表（点击勾选）</div>
        <div class="card-b" id="checkBox"></div>
      </div>
      <div class="card">
        <div class="card-h"><span class="ic orange">策</span>投递策略</div>
        <div class="card-b"><div id="stratBox"></div></div>
      </div>
    </div>
  </section>
"""

    if has_caps:
        body += f"""
  <section class="block" id="step6">
    <div class="sec-head">
      <div class="sec-num">6</div>
      <div><h2>能力迁移矩阵 · 垂类 / 通用 / 跨类三层</h2>
      <p>{esc(t['step6_sub'])}</p></div>
    </div>
    <div class="card">
      <div class="card-h"><span class="ic blue">层</span>能力结构占比（按熟练度加权）</div>
      <div class="card-b">
        <div class="cap-bar" id="capBar"></div>
        <div class="cap-legend" id="capLegend"></div>
      </div>
    </div>
    <div id="capVerdict"></div>
    <div class="cap-grid" id="capGrid"></div>
    <div class="two-col">
      <div class="card">
        <div class="card-h"><span class="ic orange">缺</span>能力缺口（按权重排序）</div>
        <div class="card-b" id="capGapBox"></div>
      </div>
      <div class="card">
        <div class="card-h"><span class="ic green">迁</span>迁移路径建议</div>
        <div class="card-b" id="capPathBox"></div>
      </div>
    </div>
    <div class="notice info"><span class="ni">ⓘ</span><div class="cap-note">
      <b>L1</b> 换行业必须重新学语境才能用；<b>L2</b> 有可交付物、可被任意行业同口径验收；
      <b>L3</b> 作用于能力本身的元能力。三层由 <b>capability_matrix.py</b> 确定性计算，
      同族跨层按 0.6 折价——数字不是估的，改完自评请重跑脚本。
    </div></div>
  </section>
"""

    body += f"""
</div>

<footer>
  <div>{esc(source_note)}</div>
  <div style="margin-top:6px">本页面为求职规划参考，岗位信息请以官方最新发布为准 · 祝你拿下心仪 offer 🚀</div>
</footer>

<div class="copied-toast" id="toast">已复制到剪贴板</div>

<script>
window.__JOBS__ = {json_for_script(jobs)};
window.__GLOBAL__ = {json_for_script(gl)};
window.__NO_REPO__ = {'true' if no_repo else 'false'};
window.__HAS_CAP__ = {'true' if has_caps else 'false'};
window.__CHK_KEY__ = {'"jt_chk_' + chk_key(title, meta) + '"'};
</script>
<script>{build_js()}</script>
</body>
</html>
"""
    return body


def build_js():
    """前端逻辑。全部挂到 window，因为内联 onclick 需要全局函数。"""
    return r"""
(function(){
  'use strict';
  // 用 getter 而不是一次性快照：便于外部替换数据后重渲染（也便于测试注入）
  function JOBS(){ return window.__JOBS__ || []; }
  function GLOBAL(){ return window.__GLOBAL__ || {}; }
  const NO_REPO = window.__NO_REPO__;
  const CHK_KEY = window.__CHK_KEY__ || 'jt_chk';
  let cur = 0;

  function esc(s){
    return String(s==null?'':s).replace(/[&<>"']/g, c => (
      {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
  // 高亮占位符：输入必须是原始文本（内部会先 esc）
  function hl(s){
    return esc(s)
      .replace(/\[待补充[^\]]*\]/g, m => '<span class="placeholder">'+m+'</span>')
      .replace(/【示例写法[^】]*】/g, m => '<span class="example">'+m+'</span>');
  }
  function bold(s){ return String(s||'').replace(/\*\*(.+?)\*\*/g,'<b>$1</b>'); }

  function renderTabs(){
    const el = document.getElementById('jobTabs');
    if(!el) return;
    el.innerHTML = JOBS().map((j,i) =>
      '<button class="tab '+(i===cur?'active':'')+'" data-i="'+i+'">'+
      '<span class="ti">'+esc(j.id||('#'+(i+1)))+'</span>'+esc(j.title||'')+'</button>').join('');
    el.querySelectorAll('.tab').forEach(b => {
      b.onclick = () => switchJob(parseInt(b.dataset.i,10));
    });
    const j = JOBS()[cur] || {};
    const meta = document.getElementById('jobMeta');
    if(meta){
      const chips = [];
      if(j.id) chips.push('<span class="chip">职位ID '+esc(j.id)+'</span>');
      if(j.city) chips.push('<span class="chip gray">'+esc(j.city)+'</span>');
      if(j.category) chips.push('<span class="chip gray">'+esc(j.category)+'</span>');
      if(j.directionLabel) chips.push('<span class="chip warn">'+esc(j.directionLabel)+'</span>');
      if(j.url) chips.push('<a class="chip link" href="'+esc(j.url)+'" target="_blank" rel="noopener">来源原页 ↗</a>');
      meta.innerHTML = '<span class="t">'+esc(j.title||'')+'</span>' + chips.join('');
    }
  }

  function renderStep1(){
    const j = JOBS()[cur] || {};
    const jd = document.getElementById('jdBox');
    const rq = document.getElementById('reqBox');
    const kw = document.getElementById('kwBox');
    if(jd) jd.innerHTML = (j.jd||[]).map(x => '<div class="jd-item">'+hl(x)+'</div>').join('');
    if(rq) rq.innerHTML = (j.req||[]).map(x => {
      const plus = /加分|优先/.test(String(x).slice(0,4)) || /^5、/.test(String(x));
      return '<div class="req-item '+(plus?'plus':'')+'">'+hl(x)+'</div>';
    }).join('');
    if(kw) kw.innerHTML = '<span class="kw-label">JD 关键词</span>' +
      (j.keywords||[]).map(k => '<span class="kw">'+esc(k)+'</span>').join('');
  }

  function renderStep2(){
    const j = JOBS()[cur] || {};
    const r = j.resume || {};
    const box = document.getElementById('resumeBox');
    if(!box) return;

    let html = '<div class="rname">[你的姓名] ' +
      '<span class="rcontact">｜' +
      esc(j.major || '[专业]') + '（' + esc(j.grade || '[届别]') + '）｜[手机]｜[邮箱]｜[作品集/GitHub]</span></div>';
    html += '<div class="rpos">' + esc(j.title||'') + ' · 定制版' +
      (j.id ? '（职位ID ' + esc(j.id) + '）' : '') + '</div>';

    if(r.positioning){
      html += '<div class="rnote">' + hl(r.positioning) + '</div>';
    }
    html += '<div class="rsum">' + hl(r.summary||'') + '</div>';

    html += '<div class="rsec"><div class="rsec-t">技能矩阵（按 JD 命中优先级排序）</div>';
    (r.skills||[]).forEach(s => {
      html += '<div class="skill-row"><div class="sk">'+esc(s.k)+'</div><div class="sv">'+hl(s.v)+'</div></div>';
    });
    html += '</div>';

    html += '<div class="rsec"><div class="rsec-t">项目经历（与岗位方向对齐）</div>';
    (r.projects||[]).forEach(p => {
      html += '<div class="proj"><div class="pn">'+hl(p.name)+'</div>' +
        '<div class="ps">'+hl(p.star)+'</div>' +
        '<div class="pb">'+hl(p.body)+'</div></div>';
    });
    html += '</div>';
    box.innerHTML = html;

    const mt = document.getElementById('matchTable');
    if(mt){
      mt.innerHTML = '<thead><tr><th style="width:42%">JD 要求</th><th>你的对应证据</th></tr></thead><tbody>' +
        (r.match||[]).map(m => '<tr><td><b>'+esc(m[0])+'</b></td><td class="ev">'+hl(m[1])+'</td></tr>').join('') +
        '</tbody>';
    }
  }

  function renderStep3(){
    const j = JOBS()[cur] || {};
    const el = document.getElementById('buildBox');
    if(!el) return;
    el.innerHTML = (j.build||[]).map(b =>
      '<div class="bcard"><span class="pb-badge pb-'+esc(b.p)+'">'+esc(b.p)+'</span>' +
      '<div><div class="bt">'+esc(b.t)+'</div><div class="bd">'+hl(b.d)+'</div></div></div>').join('');
  }

  function renderStep4(){
    if(NO_REPO) return;
    const j = JOBS()[cur] || {};
    const el = document.getElementById('repoBox');
    if(!el) return;
    const repos = j.repos || [];
    if(!repos.length){
      el.innerHTML = '<div class="notice info"><span class="ni">ℹ</span><div>' +
        '该岗位未检索到可用的二创来源。<b>不要跳过这一步</b>——换用通用来源：' +
        'GitHub 同义词搜索、Gitee、行业公开报告，或让助手按 <b>rework-matrix.md</b> 重新检索。</div></div>';
      return;
    }
    el.innerHTML = repos.map(r => {
      const chips = [];
      if(r.star) chips.push('<span class="starchip">★ '+esc(r.star)+'</span>');
      if(r.lang) chips.push('<span class="langchip">'+esc(r.lang)+'</span>');
      if(r.tag)  chips.push('<span class="tagchip">'+esc(r.tag)+'</span>');
      if(r.mode) chips.push('<span class="modechip">'+esc(r.mode)+' 模式</span>');
      return '<div class="repo"><div class="repo-h"><div>' +
        '<div class="rn">'+esc(r.name)+'</div>' +
        '<div class="rmeta">'+chips.join('')+'</div></div>' +
        '<span class="chev">▶</span></div>' +
        '<div class="repo-b"><div class="why">'+hl(r.why||'')+'</div>' +
        '<div class="fork-t">二创切入点</div>' +
        (r.fork||[]).map(f => '<div class="fork-item">'+hl(f)+'</div>').join('') +
        (r.accept ? '<div class="accept"><b>验收标准：</b>'+hl(r.accept)+'</div>' : '') +
        '</div></div>';
    }).join('');
    el.querySelectorAll('.repo').forEach(r => {
      const h = r.querySelector('.repo-h');
      if(h) h.onclick = () => r.classList.toggle('open');
    });
  }

  function loadChk(){
    try { return JSON.parse(localStorage.getItem(CHK_KEY) || '[]'); } catch(e){ return []; }
  }
  function saveChk(a){
    try { localStorage.setItem(CHK_KEY, JSON.stringify(a)); } catch(e){}
  }

  function renderStep5(){
    const rb = document.getElementById('roadmapBox');
    if(rb) rb.innerHTML = (GLOBAL().roadmap||[]).map(p =>
      '<div class="tl-item"><div class="ph">'+esc(p.phase)+'</div>' +
      '<div class="tt">'+esc(p.title)+'</div><ul>' +
      (p.items||[]).map(i => '<li>'+hl(i)+'</li>').join('') + '</ul></div>').join('');

    const ck = loadChk();
    const cb = document.getElementById('checkBox');
    if(cb){
      cb.innerHTML = (GLOBAL().checklist||[]).map((c,i) =>
        '<div class="chk '+(ck[i]?'on':'')+'" data-i="'+i+'">' +
        '<div class="box">'+(ck[i]?'✓':'')+'</div><div>'+bold(hl(c))+'</div></div>').join('');
      cb.querySelectorAll('.chk').forEach(el => {
        el.onclick = () => {
          const i = parseInt(el.dataset.i,10);
          const a = loadChk();
          a[i] = !a[i];
          saveChk(a);
          el.classList.toggle('on', !!a[i]);
          const bx = el.querySelector('.box');
          if(bx) bx.textContent = a[i] ? '✓' : '';
        };
      });
    }

    const sb = document.getElementById('stratBox');
    if(sb) sb.innerHTML = (GLOBAL().strategy||[]).map(s =>
      '<div class="scard"><div class="st">'+esc(s.t)+'</div>' +
      '<div class="sd">'+hl(s.d)+'</div></div>').join('');
  }

  function copyResume(){
    const j = JOBS()[cur] || {}, r = j.resume || {};
    let t = (j.title||'') + ' 定制简历' + (j.id ? '（'+j.id+'）' : '') + '\n\n';
    t += String(r.summary||'').replace(/\[[^\]]*\]/g,'【待你填写】') + '\n\n【技能矩阵】\n';
    (r.skills||[]).forEach(s => t += '· ' + s.k + '：' + s.v + '\n');
    t += '\n【项目经历】\n';
    (r.projects||[]).forEach(p => t += '\n▸ ' + p.name + (p.star?'（'+p.star+'）':'') + '\n' + p.body + '\n');
    t += '\n【竞赛/论文/作品/开源】\n· 【待你填写】\n';

    const done = () => {
      const el = document.getElementById('toast');
      if(el){ el.classList.add('show'); setTimeout(()=>el.classList.remove('show'), 1600); }
    };
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(t).then(done).catch(()=>fallbackCopy(t, done));
    } else { fallbackCopy(t, done); }
  }
  function fallbackCopy(text, done){
    const ta = document.createElement('textarea');
    ta.value = text; ta.style.position='fixed'; ta.style.left='-9999px';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch(e){}
    document.body.removeChild(ta); done();
  }

  // ── 第 6 步：能力迁移矩阵 ──────────────────────────────────────────
  // 数据全部来自 j.matrix（capability_matrix.py 生成），这里只做模板拼装。
  // 刻意不在 JS 里做任何算术：两份实现必然漂移，而「同一输入同一份额」是本 skill 的信任前提。
  const TIER_NAME = {L1:'垂类专属', L2:'非垂类通用', L3:'跨类迁移'};
  const TIERS = ['L1','L2','L3'];

  function renderStep6(){
    if(!window.__HAS_CAP__) return;
    const j = JOBS()[cur] || {};
    const m = j.matrix;
    const bar = document.getElementById('capBar');
    const legend = document.getElementById('capLegend');
    const verdict = document.getElementById('capVerdict');
    const grid = document.getElementById('capGrid');
    const gapBox = document.getElementById('capGapBox');
    const pathBox = document.getElementById('capPathBox');
    if(!grid) return;

    const barCard  = bar  ? bar.closest('.card')  : null;
    const gapCard  = gapBox  ? gapBox.closest('.card')  : null;
    const pathCard = pathBox ? pathBox.closest('.card') : null;
    const pair = (gapCard && gapCard.parentNode) || null;   // .two-col
    const show = (el, on) => { if(el) el.style.display = on ? '' : 'none'; };

    // 该岗位没做能力拆解 / 还没跑脚本 → 只留一条说明，不摆空壳
    if(!m || m.skipped){
      const why = (m && m.reason) ? m.reason
        : '该岗位尚未生成能力矩阵，请先运行 capability_matrix.py --merge 重算。';
      show(barCard, false); show(grid, false); show(pair, false);
      if(legend) legend.innerHTML = '';
      if(verdict){
        verdict.innerHTML = '<div class="notice info"><span class="ni">ℹ</span><div>' +
          esc(why) + '</div></div>';
      }
      return;
    }
    show(grid, true); show(pair, true);

    // ① 三层占比条（按熟练度加权，脚本已保证三项和为 100）
    const share = m.share || {};
    const shareSum = (share.L1||0) + (share.L2||0) + (share.L3||0);
    show(barCard, shareSum > 0);
    if(bar && shareSum > 0){
      bar.innerHTML = TIERS.map((k,i) => {
        const w = share[k] || 0;
        if(!w) return '';
        return '<div class="cap-seg l'+(i+1)+'" style="width:'+w+'%" title="'+
          TIER_NAME[k]+' '+w+'%"></div>';
      }).join('');
    }
    if(legend){
      legend.innerHTML = TIERS.map((k,i) => {
        const t = (m.tiers||{})[k] || {};
        const hit = (t.hit === null || t.hit === undefined) ? '—' : (t.hit + '%');
        return '<span class="cap-key l'+(i+1)+'"><b>'+k+'</b> '+TIER_NAME[k]+
          ' <span class="ch">'+(share[k]||0)+'% · 命中 '+hit+' · '+(t.req||0)+' 项</span></span>';
      }).join('');
    }

    // ② 场景结论
    if(verdict){
      const s = m.scene || {};
      const num = v => (v === null || v === undefined) ? '—' : v;
      verdict.innerHTML = '<div class="cap-verdict">' +
        '<span class="cv-code">'+esc(s.code||'—')+'</span>' +
        '<span class="cv-label">'+esc(s.label||'')+'</span>' +
        '<span class="cv-stat">匹配度 '+num(m.score)+' · 覆盖 '+num(m.coverage)+
          '% · 迁移 '+num(m.migrateRate)+'%</span>' +
        '<span class="cv-hint">'+esc(s.hint||'')+'</span>' +
        '<span class="cv-reason">'+esc(s.reason||'')+'</span>' +
        '</div>';
    }

    // ③ 三列能力卡
    const cols = m.columns || {};
    grid.innerHTML = TIERS.map((k,i) => {
      const rows = cols[k] || [];
      const head = '<div class="cap-col-h"><span class="cl">'+k+'</span>'+
        TIER_NAME[k]+'<span class="cn">'+rows.length+' 项</span></div>';
      const body = rows.length ? rows.map(c => {
        const lv = Math.max(0, Math.min(4, parseInt(c.lv,10) || 0));
        const dots = [0,1,2,3].map(n =>
          '<span class="lv-dot'+(n < lv ? ' on' : '')+'"></span>').join('');
        const scope = (c.scope||[]).map(x =>
          '<span class="cap-scope">'+esc(x)+'</span>').join('');
        return '<div class="cap-card">' +
          '<div class="ct">'+esc(c.name)+(c.hit ? '<span class="hit">JD 命中</span>' : '')+'</div>' +
          (c.def ? '<div class="cd">'+esc(c.def)+'</div>' : '') +
          '<div class="cf"><span class="lv-dots" title="熟练度 '+lv+'/4">'+dots+'</span>'+scope+'</div>' +
          (c.evidence ? '<div class="cap-ev">'+hl(c.evidence)+'</div>' : '') +
        '</div>';
      }).join('') : '<div class="cap-empty">— 该层暂无能力项</div>';
      return '<div class="cap-col c'+(i+1)+'">'+head+body+'</div>';
    }).join('');

    // ④ 缺口（脚本已按 权重↓ / 层级↑ / id↑ 排好序）
    if(gapBox){
      const gs = m.gap || [];
      gapBox.innerHTML = gs.length ? gs.map(g => {
        const cls = g.tier === 'L2' ? ' t2' : (g.tier === 'L3' ? ' t3' : '');
        return '<div class="gap-item"><span class="gap-tag'+cls+'">'+esc(g.tier)+'</span>' +
          '<span class="gn">'+esc(g.name)+'</span>' +
          '<span class="gw">需 '+g.need+' · 现 '+g.have+' · 约 '+g.weeks+' 周</span></div>';
      }).join('') :
        '<div class="notice info" style="margin-top:0"><span class="ni">✓</span>' +
        '<div>当前岗位三层均已覆盖，无硬缺口。</div></div>';
    }

    // ⑤ 迁移路径
    if(pathBox){
      const ps = m.paths || [];
      pathBox.innerHTML = ps.length ? ps.map(p =>
        '<div class="path-item"><div class="pt">'+esc(p.title)+'</div>' +
        '<div class="pj">'+esc(p.from||'')+' → '+esc(p.to||'')+
          (p.weeks ? ' · 约 '+p.weeks+' 周' : '')+'</div>' +
        '<div class="pa">'+esc(p.action||'')+'</div></div>').join('') :
        '<div class="notice info" style="margin-top:0"><span class="ni">ℹ</span>' +
        '<div>暂无路径建议。</div></div>';
    }
  }

  function switchJob(i){
    if(i < 0 || i >= JOBS().length) return;
    cur = i;
    // 第 6 步必须跟着切：三层命中率、缺口、路径都是逐岗位数据。
    // 只挂 renderAll 会让缺口清单停留在上一个岗位——页面不报错，内容却是错的。
    renderTabs(); renderStep1(); renderStep2(); renderStep3(); renderStep4(); renderStep6();
  }

  function renderAll(){
    renderTabs(); renderStep1(); renderStep2(); renderStep3();
    renderStep4(); renderStep5(); renderStep6();
  }

  // 暴露给内联 onclick（以及外部验证脚本）
  window.switchJob = switchJob;
  window.copyResume = copyResume;
  window.renderAll = renderAll;

  // 导航高亮（step6 不存在时 getElementById 返回 null，循环已安全跳过）
  const secs = ['step1','step2','step3','step4','step5','step6'];
  window.addEventListener('scroll', () => {
    let active = '';
    secs.forEach(id => {
      const el = document.getElementById(id);
      if(el && el.getBoundingClientRect().top <= 140) active = id;
    });
    document.querySelectorAll('.navlink').forEach(a => {
      a.classList.toggle('active', a.getAttribute('href') === '#' + active);
    });
  });

  const cp = document.getElementById('copyResume');
  if(cp) cp.onclick = copyResume;

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', renderAll);
  } else { renderAll(); }
  setTimeout(renderAll, 300);   // 兜底：确保延迟渲染也生效
})();
"""


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="求职简历蜕变引导页生成器")
    ap.add_argument("jobs", help="jobs.json 路径")
    ap.add_argument("out", nargs="?", help="输出 HTML 路径")
    ap.add_argument("--title", default=None)
    ap.add_argument("--subtitle", default=None)
    ap.add_argument("--theme", choices=sorted(THEMES), default=None,
                    help="主题，默认取 meta.track")
    ap.add_argument("--no-repo", action="store_true", help="跳过第 4 步")
    ap.add_argument("--no-cap", action="store_true",
                    help="跳过第 6 步（能力迁移矩阵），强制输出五步版本")
    ap.add_argument("--selftest", action="store_true", help="只校验数据，不生成")
    args = ap.parse_args()

    errs, warns = selftest(args.jobs)

    if args.selftest:
        for e in errs:
            print("ERROR  " + e)
        for w in warns:
            print("WARN   " + w)
        if errs:
            print(f"\n[x] 校验失败：{len(errs)} 个错误，{len(warns)} 个警告")
            return 1
        print(f"[✓] 校验通过（{len(warns)} 个警告）")
        return 0

    if errs:
        for e in errs:
            print("ERROR  " + e, file=sys.stderr)
        print(f"\n[x] 数据有 {len(errs)} 个错误，先修完再渲染。"
              f"（可运行 --selftest 查看全部）", file=sys.stderr)
        return 1

    if not args.out:
        print("[x] 缺少输出路径", file=sys.stderr)
        return 1

    with open(args.jobs, encoding="utf-8") as f:
        data = json.load(f)

    theme = args.theme or (data.get("meta") or {}).get("track") or "sci"
    if theme not in THEMES:
        theme = "sci"

    # 自动补 stats
    if not data.get("stats"):
        jobs = data.get("jobs") or []
        total_repos = sum(len(j.get("repos") or []) for j in jobs)
        has_caps = (not args.no_cap) and any(
            isinstance(j.get("capabilities"), dict)
            and (j["capabilities"].get("must") or j["capabilities"].get("plus"))
            for j in jobs)
        st = [{"n": str(len(jobs)), "l": "目标岗位"},
              {"n": "6" if has_caps else "5", "l": "蜕变步骤"}]
        if total_repos:
            st.append({"n": str(total_repos), "l": "二创来源"})
        if has_caps:
            n_cap = max((len((j.get("matrix") or {}).get("columns", {}).get(t) or [])
                         for j in jobs for t in ("L1", "L2", "L3")), default=0)
            if n_cap:
                st.append({"n": str(n_cap), "l": "能力项/层"})
        if (data.get("global") or {}).get("roadmap"):
            st.append({"n": str(len(data["global"]["roadmap"])), "l": "执行阶段"})
        data["stats"] = st

    for w in warns:
        print("WARN   " + w, file=sys.stderr)

    html_out = build_html(data, theme, args.title, args.subtitle,
                          args.no_repo, args.no_cap)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"[✓] 已生成：{args.out}")
    ds_name = design_systems.system_meta(theme)["name"]
    print(f"    主题 {theme}（{THEMES[theme]['label']}）· 视觉系统 {ds_name} · "
          f"{len(data.get('jobs') or [])} 个岗位 · {len(html_out):,} 字符")
    print(f"    生成日期 {date.today().isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

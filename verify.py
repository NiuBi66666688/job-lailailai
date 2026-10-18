#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""job-lailailai 迁移包验收脚本。

迁移到新环境后，第一步就跑这个：一次性跑完六个脚本的自检 + 包完整性检查
+ 三级能力矩阵端到端 + 三主题真实渲染。零第三方依赖，纯标准库，任何有
Python 3.8+ 的环境都能跑。

    python verify.py
"""

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
SAMPLE = ROOT / "examples" / "jobs.sample.json"
PROFILE = ROOT / "examples" / "profile.sample.json"
TIERS_DOC = ROOT / "references" / "capability-tiers.md"

# 包内必须存在的文件（相对包根）
REQUIRED = [
    "SKILL.md",
    "AGENTS.md",
    "README.md",
    "requirements.txt",
    "references/capability-tiers.md",
    "references/data-contract.md",
    "references/design-systems.md",
    "references/portability.md",
    "references/resume-rules.md",
    "references/rework-matrix.md",
    "references/search-recipes.md",
    "references/track-dimensions.md",
    "references/verify-render.md",
    "scripts/capability_matrix.py",
    "scripts/design_systems.py",
    "scripts/install.py",
    "scripts/match_score.py",
    "scripts/render.py",
    "scripts/split_jd.py",
    "examples/jobs.sample.json",
    "examples/profile.sample.json",
    "examples/demo.html",
]


def check_required():
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    return (not missing), (f"缺失 {len(missing)} 个：{', '.join(missing)}" if missing
                           else f"{len(REQUIRED)} 个必要文件齐全")


def check_deps():
    """确认所有脚本只 import 标准库（本目录内的模块不算第三方）。"""
    stdlib_ok = True
    third_party = set()
    # 标准库 + 本目录内的自有模块
    local = {"argparse", "os", "sys", "json", "re", "html", "shutil", "math",
             "pathlib", "hashlib", "subprocess", "datetime", "zipfile",
             "design_systems", "capability_matrix"}
    for f in sorted(SCRIPTS.glob("*.py")):
        for line in f.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            mod = None
            if s.startswith("import "):
                mod = s[7:].split()[0].split(".")[0]
            elif s.startswith("from "):
                mod = s[5:].split()[0].split(".")[0]
            if mod and mod not in local and not mod.startswith("_"):
                third_party.add(f"{f.name}:{mod}")
                stdlib_ok = False
    return stdlib_ok, ("零第三方依赖" if stdlib_ok
                       else "发现非标准库导入：" + ", ".join(sorted(third_party)))


def run_selftest(name, args):
    script = SCRIPTS / name
    try:
        r = subprocess.run(
            [sys.executable, str(script)] + args,
            capture_output=True, text=True, encoding="utf-8", timeout=120,
            cwd=str(ROOT),
        )
    except Exception as e:
        return False, f"执行异常：{e}"
    tail = (r.stdout or "").strip().splitlines()
    last = tail[-1] if tail else "(无输出)"
    if r.returncode != 0:
        return False, f"退出码 {r.returncode}｜{last}"
    if "[✗]" in (r.stdout or ""):
        return False, f"自检含失败项｜{last}"
    return True, last


def check_manifest():
    mf = ROOT / "MANIFEST.txt"
    if not mf.exists():
        return True, "无 MANIFEST.txt（跳过校验）"
    bad = []
    n = 0
    for line in mf.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        digest, rel = parts[0], parts[1].strip()
        p = ROOT / rel
        n += 1
        if not p.exists():
            bad.append(f"{rel}(缺失)")
            continue
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual != digest:
            bad.append(f"{rel}(校验和不符)")
    if bad:
        return False, f"{len(bad)}/{n} 个文件校验失败：{', '.join(bad[:5])}"
    return True, f"{n} 个文件校验和全部匹配"


def check_catalog_sync():
    """references/capability-tiers.md 的 id 集合必须与 CATALOG 完全一致。

    文档是给人和模型看的，代码是给机器算的；两边一旦分叉，模型会照文档写
    一个脚本不认识的 id，而脚本只会静默忽略——用户看到的是「能力项凭空消失」。
    """
    try:
        sys.path.insert(0, str(SCRIPTS))
        import capability_matrix as cm  # noqa: E402
    except Exception as e:
        return False, f"无法导入 capability_matrix：{e}"
    finally:
        if str(SCRIPTS) in sys.path:
            sys.path.remove(str(SCRIPTS))

    if not TIERS_DOC.exists():
        return False, "缺少 references/capability-tiers.md"

    text = TIERS_DOC.read_text(encoding="utf-8")
    documented = set(re.findall(r"\bL[123]-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*\b", text))
    catalog = set(cm.CATALOG)

    missing_doc = sorted(catalog - documented)
    extra_doc = sorted(documented - catalog)
    if missing_doc or extra_doc:
        bits = []
        if missing_doc:
            bits.append("文档未收录：" + ", ".join(missing_doc))
        if extra_doc:
            bits.append("文档多出：" + ", ".join(extra_doc))
        return False, "｜".join(bits)
    return True, f"{len(catalog)} 项 id 与文档完全一致（catalogVersion {cm.CATALOG_VERSION}）"


def check_js_wiring():
    """renderStep6 必须同时挂在 renderAll 与 switchJob 上。

    只挂 renderAll 是典型的静默失败：页面不报错，但切岗位后第 6 步仍停在
    上一个岗位的数字——用户看不出错，结论却是错的。源码层面直接断言。
    """
    src = (SCRIPTS / "render.py").read_text(encoding="utf-8")

    def body_of(name):
        m = re.search(r"\n  function %s\([^)]*\)\{" % name, src)
        if not m:
            return None
        start = m.end()
        end = src.find("\n  function ", start)
        return src[start:end if end != -1 else len(src)]

    problems = []
    if not re.search(r"\n  function renderStep6\(\)\{", src):
        problems.append("未定义 renderStep6()")
    for fn in ("renderAll", "switchJob"):
        b = body_of(fn)
        if b is None:
            problems.append(f"未找到 {fn}()")
        elif "renderStep6()" not in b:
            problems.append(f"{fn}() 未调用 renderStep6()")
    if "--no-cap" not in src:
        problems.append("缺少 --no-cap 降级开关")
    if problems:
        return False, "｜".join(problems)
    return True, "renderStep6 已挂 renderAll + switchJob，含 --no-cap 降级"


def check_matrix_e2e():
    """profile + jobs → capability_matrix --merge → 校验矩阵自洽 → 渲染出第 6 步。"""
    if not PROFILE.exists():
        return False, "缺少 examples/profile.sample.json"
    tmp = Path(tempfile.mkdtemp(prefix="jll_"))
    merged = tmp / "jobs.merged.json"
    html_out = tmp / "out.html"
    try:
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / "capability_matrix.py"),
             "--profile", str(PROFILE), "--jobs", str(SAMPLE),
             "--merge", "--out", str(merged)],
            capture_output=True, text=True, encoding="utf-8", timeout=180, cwd=str(ROOT),
        )
        if r.returncode != 0 or not merged.exists():
            return False, f"矩阵生成失败｜{(r.stderr or r.stdout or '').strip()[:120]}"

        data = json.loads(merged.read_text(encoding="utf-8"))
        jobs = data.get("jobs") or []
        with_caps = [j for j in jobs if isinstance(j.get("capabilities"), dict)
                     and (j["capabilities"].get("must") or j["capabilities"].get("plus"))]
        if not with_caps:
            return False, "样例里没有任何岗位带 capabilities"

        for j in with_caps:
            m = j.get("matrix")
            if not isinstance(m, dict):
                return False, f"{j.get('id')} 未生成 matrix"
            share = m.get("share") or {}
            total = sum(int(share.get(k) or 0) for k in ("L1", "L2", "L3"))
            if total not in (0, 100):
                return False, f"{j.get('id')} share 三项和为 {total}，应为 0 或 100"
            if not (m.get("scene") or {}).get("code"):
                return False, f"{j.get('id')} 缺少 scene.code"

        r2 = subprocess.run(
            [sys.executable, str(SCRIPTS / "render.py"), str(merged), str(html_out)],
            capture_output=True, text=True, encoding="utf-8", timeout=180, cwd=str(ROOT),
        )
        if r2.returncode != 0 or not html_out.exists():
            return False, f"渲染失败｜{(r2.stderr or r2.stdout or '').strip()[:120]}"
        text = html_out.read_text(encoding="utf-8")
        if 'id="step6"' not in text:
            return False, "产出页面里没有第 6 步（能力矩阵未接线）"
        return True, f"{len(with_caps)} 个岗位矩阵自洽 · 第 6 步已渲染"
    except Exception as e:
        return False, f"异常：{e}"
    finally:
        try:
            for p in tmp.iterdir():
                p.unlink()
            tmp.rmdir()
        except Exception:
            pass


def _lum(hexstr):
    """sRGB 相对亮度。用于断言三层能力色明度严格递增。"""
    h = hexstr.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return None
    try:
        ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    except ValueError:
        return None
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _smoke(track, expect_accent):
    """单个主题的真实渲染冒烟：token 完整性 + 设计系统绑定 + 第 6 步结构。"""
    out = ROOT / "examples" / f"_verify_{track}.html"
    try:
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / "render.py"), str(SAMPLE), str(out),
             "--theme", track],
            capture_output=True, text=True, encoding="utf-8", timeout=180,
            cwd=str(ROOT),
        )
        if r.returncode != 0 or not out.exists() or out.stat().st_size < 1000:
            return False, "渲染失败"
        text = out.read_text(encoding="utf-8")
        defined = set(re.findall(r"^\s*(--[a-z0-9-]+)\s*:", text, flags=re.M))
        used = set(re.findall(r"var\((--[a-z0-9-]+)\)", text))
        undef = sorted(used - defined)
        if undef:
            return False, f"引用了未定义的 token：{', '.join(undef[:4])}"
        if f"--accent: {expect_accent}" not in text:
            return False, f"未用上 {track} 对应的设计系统强调色 {expect_accent}"

        # 第 6 步必须真的出现（样例带 capabilities）
        if 'id="step6"' not in text or "六步法" not in text:
            return False, "第 6 步未渲染（样例含 capabilities 时应为六步法）"

        # 三层能力色必须定义齐全且明度严格递增，否则「L1 最深→L3 最浅」的深度语义失效
        lums = []
        for i in (1, 2, 3):
            m = re.search(r"^\s*--cap-l%d:\s*(#[0-9a-fA-F]{3,6})\s*;" % i, text, flags=re.M)
            if not m:
                return False, f"缺少 --cap-l{i} token"
            v = _lum(m.group(1))
            if v is None:
                return False, f"--cap-l{i} 不是合法色值：{m.group(1)}"
            lums.append(v)
        if not (lums[0] < lums[1] < lums[2]):
            return False, ("三层能力色明度未递增："
                           + " > ".join(f"{v:.3f}" for v in lums))

        return True, (f"{out.stat().st_size:,} 字节 · {len(defined)} 个 token 全部有定义 · "
                      f"能力三层明度 {'<'.join(f'{v:.2f}' for v in lums)}")
    except Exception as e:
        return False, f"异常：{e}"
    finally:
        if out.exists():
            out.unlink()


def check_nocap_compat():
    """--no-cap 必须干净退回五步版本（老数据 / 用户不做盘点的兼容路径）。"""
    out = ROOT / "examples" / "_verify_nocap.html"
    try:
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / "render.py"), str(SAMPLE), str(out),
             "--theme", "sci", "--no-cap"],
            capture_output=True, text=True, encoding="utf-8", timeout=180,
            cwd=str(ROOT),
        )
        if r.returncode != 0 or not out.exists():
            return False, "渲染失败"
        text = out.read_text(encoding="utf-8")
        if 'id="step6"' in text:
            return False, "--no-cap 下仍渲染了第 6 步"
        nav = len(re.findall(r'class="navlink', text))
        if nav != 5:
            return False, f"--no-cap 下导航项为 {nav}，应为 5"
        return True, "已退回五步法（5 个导航项，无第 6 步）"
    except Exception as e:
        return False, f"异常：{e}"
    finally:
        if out.exists():
            out.unlink()


def main():
    print("=" * 62)
    print(" job-lailailai 迁移包验收")
    print(f" 包根目录：{ROOT}")
    print(f" Python  ：{sys.version.split()[0]}  ({sys.executable})")
    print("=" * 62)

    checks = [
        ("包完整性", check_required),
        ("依赖检查", check_deps),
        ("校验和清单", check_manifest),
        ("能力目录一致性", check_catalog_sync),
        ("第 6 步接线检查", check_js_wiring),
        ("design_systems.py 自检",
         lambda: run_selftest("design_systems.py", [])),
        ("install.py 自检", lambda: run_selftest("install.py", ["--selftest"])),
        ("match_score.py 自检", lambda: run_selftest("match_score.py", ["--selftest"])),
        ("split_jd.py 自检", lambda: run_selftest("split_jd.py", ["--selftest"])),
        ("capability_matrix.py 自检",
         lambda: run_selftest("capability_matrix.py", ["--selftest"])),
        ("render.py 数据契约校验",
         lambda: run_selftest("render.py", ["--selftest", str(SAMPLE)])),
        ("能力矩阵端到端", check_matrix_e2e),
    ]

    allok = True
    for name, fn in checks:
        try:
            ok, info = fn()
        except Exception as e:
            ok, info = False, f"异常：{e}"
        print(f"[{'✓' if ok else '✗'}] {name:<22} {info}")
        allok = allok and ok

    # 附加：三个主题各真实渲染一次（含第 6 步与三层色阶断言）+ 五步兼容路径
    print("-" * 62)
    for track, expect_accent in (("sci", "#0070f3"), ("art", "#9a5a2f"), ("biz", "#533afd")):
        try:
            ok, info = _smoke(track, expect_accent)
        except Exception as e:
            ok, info = False, f"异常：{e}"
        print(f"[{'✓' if ok else '✗'}] {'渲染冒烟 · ' + track:<20} {info}")
        allok = allok and ok

    try:
        ok, info = check_nocap_compat()
    except Exception as e:
        ok, info = False, f"异常：{e}"
    print(f"[{'✓' if ok else '✗'}] {'五步兼容路径':<20} {info}")
    allok = allok and ok

    print("=" * 62)
    print("[✓] 验收通过：本包在新环境可直接使用" if allok
          else "[✗] 存在失败项，请先修复再使用")
    print("=" * 62)
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())

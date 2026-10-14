#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""job-lailailai 迁移包验收脚本。

迁移到新环境后，第一步就跑这个：一次性跑完四个脚本的自检 + 包完整性检查。
零第三方依赖，纯标准库，任何有 Python 3.8+ 的环境都能跑。

    python verify.py
"""

import hashlib
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
SAMPLE = ROOT / "examples" / "jobs.sample.json"

# 包内必须存在的文件（相对包根）
REQUIRED = [
    "SKILL.md",
    "AGENTS.md",
    "README.md",
    "requirements.txt",
    "references/data-contract.md",
    "references/design-systems.md",
    "references/portability.md",
    "references/resume-rules.md",
    "references/rework-matrix.md",
    "references/search-recipes.md",
    "references/track-dimensions.md",
    "references/verify-render.md",
    "scripts/design_systems.py",
    "scripts/install.py",
    "scripts/match_score.py",
    "scripts/render.py",
    "scripts/split_jd.py",
    "examples/jobs.sample.json",
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
    local = {"argparse", "os", "sys", "json", "re", "html", "shutil",
             "pathlib", "hashlib", "subprocess", "datetime", "zipfile",
             "design_systems"}
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
        ("design_systems.py 自检",
         lambda: run_selftest("design_systems.py", [])),
        ("install.py 自检", lambda: run_selftest("install.py", ["--selftest"])),
        ("match_score.py 自检", lambda: run_selftest("match_score.py", ["--selftest"])),
        ("split_jd.py 自检", lambda: run_selftest("split_jd.py", ["--selftest"])),
        ("render.py 数据契约校验",
         lambda: run_selftest("render.py", ["--selftest", str(SAMPLE)])),
    ]

    allok = True
    for name, fn in checks:
        try:
            ok, info = fn()
        except Exception as e:
            ok, info = False, f"异常：{e}"
        print(f"[{'✓' if ok else '✗'}] {name:<22} {info}")
        allok = allok and ok

    # 附加：三个主题各真实渲染一次，并校验 token 引用完整性
    print("-" * 62)
    for track, expect_accent in (("sci", "#0070f3"), ("art", "#9a5a2f"), ("biz", "#533afd")):
        out = ROOT / "examples" / f"_verify_{track}.html"
        label = f"渲染冒烟 · {track}"
        try:
            r = subprocess.run(
                [sys.executable, str(SCRIPTS / "render.py"), str(SAMPLE), str(out),
                 "--theme", track],
                capture_output=True, text=True, encoding="utf-8", timeout=180,
                cwd=str(ROOT),
            )
            if r.returncode != 0 or not out.exists() or out.stat().st_size < 1000:
                ok, info = False, "渲染失败"
            else:
                text = out.read_text(encoding="utf-8")
                defined = set(re.findall(r"^\s*(--[a-z0-9-]+)\s*:", text, flags=re.M))
                used = set(re.findall(r"var\((--[a-z0-9-]+)\)", text))
                undef = sorted(used - defined)
                if undef:
                    ok, info = False, f"引用了未定义的 token：{', '.join(undef[:4])}"
                elif f"--accent: {expect_accent}" not in text:
                    ok, info = False, f"未用上 {track} 对应的设计系统强调色 {expect_accent}"
                else:
                    ok = True
                    info = (f"{out.stat().st_size:,} 字节 · "
                            f"{len(defined)} 个 token 全部有定义")
        except Exception as e:
            ok, info = False, f"异常：{e}"
        finally:
            if out.exists():
                out.unlink()
        print(f"[{'✓' if ok else '✗'}] {label:<20} {info}")
        allok = allok and ok

    print("=" * 62)
    print("[✓] 验收通过：本包在新环境可直接使用" if allok
          else "[✗] 存在失败项，请先修复再使用")
    print("=" * 62)
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())

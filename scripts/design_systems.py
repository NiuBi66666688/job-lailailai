#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设计系统 token 层 —— 引导页的视觉地基。

三个学科轨道各自绑定一套真实的设计系统（来自 OpenDesign 设计系统包，
Apache-2.0）：

    sci（理工科）  ->  Vercel     近白画布 / 近黑文字 / 单一蓝强调 / shadow-as-border
    art（人文社科）->  Editorial  暖纸面 / 衬线标题 / 赭石强调 / 单层柔和投影
    biz（经管商科）->  Stripe     白底 / 藏青文字 / 紫罗兰强调 / 多层蓝调投影

上游：https://github.com/nexu-io/open-design
      design-systems/{vercel,editorial,stripe}/tokens.css

## 为什么要把 tokens.css 搬进 Python

上游 tokens.css 是给 agent「粘贴进 artifact 的 :root 块」用的。这里做了两件
事，都是为了产出物更稳：

1. **预编译**：把 `:root` 块变成 Python 字典，主题切换 = 换一个字典。
   新增主题只需在 SYSTEMS 里登记，不必改 render.py 的 CSS。
2. **预解析 color-mix()**：上游用 `color-mix(in oklab, var(--accent), black 8%)`
   表达 hover 态。这需要 Chrome 111+ / Safari 16.2+。产出物要「双击即开」，
   所以这里在构建期用 oklab 算成具体色值，不把兼容性押在浏览器版本上。

## 与上游的差异（有意为之，逐条可查）

- `--surface-2`：OD schema 里 Vercel 的 `--surface-warm` 别名到 `--surface`
  （同为纯白）。长页面需要「交替层」来分隔区块，纯白会丢失层次，因此这里
  为 Vercel 取 gray-50 `#fafafa` 作为 `--surface-2`。Editorial 与 Stripe
  的 `--surface-warm` 本身就有区分度，直接沿用。
- **派生色**（`--accent-soft` / `--success-soft` / `--warn-soft` /
  `--danger-soft` / `--p0..--p2`）：OD schema 只给实色，不给浅底。这些按
  「角色色 × 白 8%」在 oklab 空间派生，保证与主色同源而非各调各的。
- **中文字体回退**：上游字体栈是拉丁字体，中文会掉到系统默认。这里在每个
  字体栈尾部接上中文回退（无衬线接 PingFang / 微软雅黑，衬线接宋体）。
- `--tracking-display` 只作用于展示级标题，正文不做负字距，避免中文发挤。
"""

# ---------------------------------------------------------------------------
# 颜色工具：oklab 混合（与 CSS color-mix(in oklab, ...) 同算法）
# ---------------------------------------------------------------------------

def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02x}" for c in rgb)


def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def _linear_to_oklab(r, g, b):
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def _oklab_to_linear(L, a, b):
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return (
        +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def mix_oklab(hex_a, hex_b, t):
    """把 hex_b 以权重 t 混进 hex_a（t=0 全 a，t=1 全 b）。等价 CSS color-mix。"""
    ra, ga, ba = (_srgb_to_linear(c) for c in _hex_to_rgb(hex_a))
    rb, gb, bb = (_srgb_to_linear(c) for c in _hex_to_rgb(hex_b))
    A, B = _linear_to_oklab(ra, ga, ba), _linear_to_oklab(rb, gb, bb)
    mixed = tuple(x + (y - x) * t for x, y in zip(A, B))
    r, g, b = _oklab_to_linear(*mixed)
    return _rgb_to_hex((_linear_to_srgb(r), _linear_to_srgb(g), _linear_to_srgb(b)))


def shade(hex_color, black_pct):
    """等价 color-mix(in oklab, hex_color, black black_pct%)。"""
    return mix_oklab(hex_color, "#000000", black_pct / 100.0)


def tint(hex_color, amount=0.08, base="#ffffff"):
    """角色色铺成浅底：amount 为角色色占比（默认 8%）。"""
    return mix_oklab(base, hex_color, amount)


def rgba(hex_color, alpha):
    r, g, b = (round(c * 255) for c in _hex_to_rgb(hex_color))
    return f"rgba({r}, {g}, {b}, {alpha})"


# ---------------------------------------------------------------------------
# 设计系统 token（取自上游 tokens.css 的 :root 块）
# ---------------------------------------------------------------------------

_FALLBACK_SANS = ('"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", '
                  '"Noto Sans SC", sans-serif')
_FALLBACK_SERIF = '"Songti SC", "SimSun", "Noto Serif SC", serif'


def _vercel():
    a = "#0070f3"
    return {
        "_meta": {
            "slug": "vercel", "name": "Vercel",
            "voice": "工程即设计：近白画布、近黑文字、单一蓝强调、以阴影充当描边",
            "upstream": "https://github.com/nexu-io/open-design/tree/main/design-systems/vercel",
        },
        "bg": "#ffffff",
        "surface": "#ffffff",
        "surface-2": "#fafafa",            # 派生：OD 的 --surface-warm 别名到纯白，此处取 gray-50 补交替层
        "fg": "#171717",
        "fg-2": "#4d4d4d",
        "muted": "#666666",
        "meta": "#808080",
        "border": "rgba(0, 0, 0, 0.08)",
        "border-soft": "rgba(0, 0, 0, 0.04)",
        "accent": a,
        "accent-on": "#ffffff",
        "accent-hover": shade(a, 8),
        "accent-active": shade(a, 14),
        "success": "#16a34a",
        "warn": "#eab308",
        "danger": "#dc2626",
        "font-display": f'"Geist", "Geist Sans", -apple-system, "Segoe UI", Arial, {_FALLBACK_SANS}',
        "font-body": f'"Geist", "Geist Sans", -apple-system, "Segoe UI", Arial, {_FALLBACK_SANS}',
        "font-mono": '"Geist Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace',
        "text-xs": "12px", "text-sm": "14px", "text-base": "16px",
        "text-lg": "20px", "text-xl": "24px", "text-2xl": "32px",
        "text-3xl": "40px", "text-4xl": "48px",
        "leading-body": "1.5", "leading-tight": "1.1", "tracking-display": "-0.05em",
        "section-y-desktop": "96px", "section-y-tablet": "64px", "section-y-phone": "48px",
        "radius-sm": "6px", "radius-md": "8px", "radius-lg": "12px", "radius-pill": "9999px",
        "elev-flat": "none",
        "elev-ring": "0 0 0 1px var(--border)",
        "elev-raised": ("0 0 0 1px rgba(0, 0, 0, 0.08), 0 2px 2px rgba(0, 0, 0, 0.04), "
                        "0 8px 8px -8px rgba(0, 0, 0, 0.04)"),
        "focus-ring": "0 0 0 2px var(--accent)",
        "motion-fast": "150ms", "motion-base": "200ms",
        "ease-standard": "cubic-bezier(0.2, 0, 0, 1)",
        "container-max": "1200px",
        "container-gutter-desktop": "24px",
        "container-gutter-tablet": "16px",
        "container-gutter-phone": "12px",
    }


def _editorial():
    a = "#9a5a2f"
    return {
        "_meta": {
            "slug": "editorial", "name": "Editorial",
            "voice": "出版物的编排语言：暖纸面、衬线标题、赭石强调、单层柔和投影",
            "upstream": "https://github.com/nexu-io/open-design/tree/main/design-systems/editorial",
        },
        "bg": "#fbf7f0",
        "surface": "#fffdf8",
        "surface-2": "#f1e6d6",
        "fg": "#1f1a16",
        "fg-2": "#4b4038",
        "muted": "#7d7168",
        "meta": "#9a5a2f",
        "border": "#ded3c5",
        "border-soft": "#eee5da",
        "accent": a,
        "accent-on": "#ffffff",
        "accent-hover": shade(a, 8),
        "accent-active": shade(a, 14),
        "success": "#4f8a4f",
        "warn": "#c9822f",
        "danger": "#b33a3a",
        "font-display": f'Georgia, "Times New Roman", {_FALLBACK_SERIF}',
        "font-body": f'"Source Serif Pro", Georgia, {_FALLBACK_SERIF}',
        "font-mono": '"IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace',
        "text-xs": "12px", "text-sm": "14px", "text-base": "18px",
        "text-lg": "21px", "text-xl": "30px", "text-2xl": "44px",
        "text-3xl": "66px", "text-4xl": "92px",
        "leading-body": "1.65", "leading-tight": "1", "tracking-display": "-0.02em",
        "section-y-desktop": "112px", "section-y-tablet": "80px", "section-y-phone": "56px",
        "radius-sm": "4px", "radius-md": "8px", "radius-lg": "12px", "radius-pill": "9999px",
        "elev-flat": "none",
        "elev-ring": "0 0 0 1px var(--border)",
        "elev-raised": "0 20px 50px rgba(31, 26, 22, 0.12)",
        "focus-ring": f"0 0 0 4px {rgba(a, 0.24)}",
        "motion-fast": "180ms", "motion-base": "280ms",
        "ease-standard": "cubic-bezier(0.22, 1, 0.36, 1)",
        "container-max": "1120px",
        "container-gutter-desktop": "36px",
        "container-gutter-tablet": "24px",
        "container-gutter-phone": "16px",
    }


def _stripe():
    a = "#533afd"
    return {
        "_meta": {
            "slug": "stripe", "name": "Stripe",
            "voice": "金融基础设施的克制表达：白底、藏青文字、紫罗兰强调、多层蓝调投影",
            "upstream": "https://github.com/nexu-io/open-design/tree/main/design-systems/stripe",
        },
        "bg": "#ffffff",
        "surface": "#ffffff",
        "surface-2": "#f6f9fc",
        "fg": "#061b31",
        "fg-2": "#273951",
        "muted": "#64748d",
        "meta": "#64748d",
        "border": "#e5edf5",
        "border-soft": "#e5edf5",
        "accent": a,
        "accent-on": "#ffffff",
        "accent-hover": "#4434d4",
        "accent-active": "#2e2b8c",
        "success": "#15be53",
        "warn": "#9b6829",
        "danger": "#ea2261",
        "font-display": (f'"sohne-var", "Söhne", "SF Pro Display", -apple-system, '
                         f'BlinkMacSystemFont, system-ui, "Helvetica Neue", Arial, {_FALLBACK_SANS}'),
        "font-body": (f'"sohne-var", "Söhne", "SF Pro Display", -apple-system, '
                      f'BlinkMacSystemFont, system-ui, "Helvetica Neue", Arial, {_FALLBACK_SANS}'),
        "font-mono": ('"Source Code Pro", ui-monospace, "SF Mono", "JetBrains Mono", '
                      'Menlo, Consolas, monospace'),
        "text-xs": "12px", "text-sm": "14px", "text-base": "16px",
        "text-lg": "18px", "text-xl": "22px", "text-2xl": "32px",
        "text-3xl": "48px", "text-4xl": "56px",
        "leading-body": "1.40", "leading-tight": "1.10", "tracking-display": "-0.02em",
        "section-y-desktop": "96px", "section-y-tablet": "64px", "section-y-phone": "40px",
        "radius-sm": "4px", "radius-md": "6px", "radius-lg": "8px", "radius-pill": "9999px",
        "elev-flat": "none",
        "elev-ring": "0 0 0 1px var(--border)",
        "elev-raised": ("rgba(50, 50, 93, 0.25) 0px 30px 45px -30px, "
                        "rgba(0, 0, 0, 0.10) 0px 18px 36px -18px"),
        "focus-ring": ("0 0 0 2px var(--accent), "
                       "0 0 0 5px " + rgba(a, 0.25)),
        "motion-fast": "150ms", "motion-base": "200ms",
        "ease-standard": "cubic-bezier(0.2, 0, 0, 1)",
        "container-max": "1080px",
        "container-gutter-desktop": "32px",
        "container-gutter-tablet": "24px",
        "container-gutter-phone": "16px",
    }


SYSTEMS = {
    "vercel": _vercel,
    "editorial": _editorial,
    "stripe": _stripe,
}

# 学科轨道 -> 设计系统。选型理由见模块 docstring 与 references/design-systems.md
TRACK_SYSTEM = {"sci": "vercel", "art": "editorial", "biz": "stripe"}

# 间距刻度三套一致，抽出来共用
SPACING = {
    "space-1": "4px", "space-2": "8px", "space-3": "12px", "space-4": "16px",
    "space-5": "20px", "space-6": "24px", "space-8": "32px", "space-12": "48px",
}


def system_for_track(track):
    """轨道名 -> 设计系统 slug（未知轨道回退 sci）。"""
    return TRACK_SYSTEM.get(track, TRACK_SYSTEM["sci"])


def system_meta(track):
    """轨道名 -> 该轨道所用设计系统的元信息（name / voice / upstream / slug）。"""
    return SYSTEMS[system_for_track(track)]()["_meta"]


def tokens_for(track):
    """取某轨道的完整 token 字典（含派生色）。"""
    t = dict(SYSTEMS[system_for_track(track)]())
    t.update(SPACING)

    # ── 派生：浅底色阶（角色色 × 主题 surface，保证与底色同源）───────
    surf = t["surface"]
    t["accent-soft"] = tint(t["accent"], 0.08, surf)
    t["success-soft"] = tint(t["success"], 0.08, surf)
    t["warn-soft"] = tint(t["warn"], 0.08, surf)
    t["danger-soft"] = tint(t["danger"], 0.08, surf)
    t["fg-soft"] = tint(t["fg"], 0.05, surf)

    # ── 派生：P0/P1/P2 优先级（复用角色色，不另造色）─────────────────
    t["p0"], t["p0-soft"] = t["danger"], t["danger-soft"]
    t["p1"], t["p1-soft"] = t["warn"], t["warn-soft"]
    t["p2"], t["p2-soft"] = t["accent"], t["accent-soft"]

    # ── 派生：命中关键词高亮（JD 关键词命中标记）─────────────────────
    t["mark-bg"] = t["accent-soft"]
    t["mark-line"] = t["accent"]

    # ── 派生：软底上的文字色 ─────────────────────────────────────────
    # 角色色直接当文字压在自身浅底上对比度不足（尤其 Vercel 的 #eab308 亮黄），
    # 因此把角色色朝主题文字色混 35% —— 在浅色主题里即「压深」，且与主题同源。
    for role in ("accent", "success", "warn", "danger"):
        t[f"{role}-ink"] = mix_oklab(t[role], t["fg"], 0.35)
    t["p0-ink"], t["p1-ink"], t["p2-ink"] = (
        t["danger-ink"], t["warn-ink"], t["accent-ink"])

    # ── 派生：能力三层（L1/L2/L3）──────────────────────────────────────
    # 三层不是三个类别，是同一能力谱系的三段深度。因此用**同一色相的三级明度**
    # 表达「越靠 L1 越深」，而不是三个语义色——后者会被误读为三类互不相干的能力，
    # 也违反「禁双品牌色」。也不复用 p0/p1/p2：那是项目优先级，语义会串味
    # （且 p0=danger 会让「垂类深度」看起来像告警）。
    t["cap-l1"] = t["accent"]
    t["cap-l2"] = mix_oklab(t["accent"], surf, 0.30)
    t["cap-l3"] = mix_oklab(t["accent"], surf, 0.55)
    for k in ("cap-l1", "cap-l2", "cap-l3"):
        t[f"{k}-soft"] = tint(t[k], 0.08, surf)
        t[f"{k}-ink"] = mix_oklab(t[k], t["fg"], 0.35)
    t["cap-rail"] = t["border"]

    # ── 派生：半透明表面（吸顶导航需要透出下层内容）──────────────────
    t["surface-translucent"] = rgba(t["surface"], 0.86)

    # ── 派生：页脚/时间轴等需要的中性线 ──────────────────────────────
    t["accent-quiet"] = shade(t["accent"], 12)
    return t


def css_root(track, indent="  "):
    """产出 `:root{...}` 声明块（不含选择器），供内联进产出 HTML。"""
    t = tokens_for(track)
    meta = t.pop("_meta")
    lines = []
    for k, v in t.items():
        lines.append(f"{indent}--{k}: {v};")
    return "\n".join(lines), meta


def selftest():
    """自检：token 完整性与 oklab 计算正确性。"""
    checks = []
    required = [
        "bg", "surface", "surface-2", "fg", "fg-2", "muted", "meta",
        "border", "border-soft", "accent", "accent-on", "accent-hover",
        "accent-active", "success", "warn", "danger",
        "font-display", "font-body", "font-mono",
        "text-xs", "text-sm", "text-base", "text-lg", "text-xl",
        "text-2xl", "text-3xl", "text-4xl",
        "leading-body", "leading-tight", "tracking-display",
        "space-1", "space-2", "space-3", "space-4", "space-5", "space-6",
        "space-8", "space-12",
        "section-y-desktop", "section-y-tablet", "section-y-phone",
        "radius-sm", "radius-md", "radius-lg", "radius-pill",
        "elev-flat", "elev-ring", "elev-raised", "focus-ring",
        "motion-fast", "motion-base", "ease-standard",
        "container-max", "container-gutter-desktop", "container-gutter-tablet",
        "container-gutter-phone",
        "accent-soft", "success-soft", "warn-soft", "danger-soft",
        "accent-ink", "success-ink", "warn-ink", "danger-ink",
        "surface-translucent",
        "p0", "p0-soft", "p1", "p1-soft", "p2", "p2-soft",
        "p0-ink", "p1-ink", "p2-ink",
        "mark-bg", "mark-line",
        "cap-l1", "cap-l2", "cap-l3",
        "cap-l1-soft", "cap-l2-soft", "cap-l3-soft",
        "cap-l1-ink", "cap-l2-ink", "cap-l3-ink",
        "cap-rail",
    ]
    for track in ("sci", "art", "biz"):
        t = tokens_for(track)
        missing = [k for k in required if k not in t]
        checks.append((f"{track} token 齐全（{len(required)} 项）", not missing,
                       ", ".join(missing) if missing else t["_meta"]["name"]))

    # oklab 正确性：混 100% 等于自身；混 0% 等于底
    checks.append(("oklab 混 0%/100% 端点正确",
                   mix_oklab("#0070f3", "#000000", 0) == "#0070f3"
                   and mix_oklab("#0070f3", "#000000", 1) == "#000000",
                   f"{mix_oklab('#0070f3', '#000000', 0)} / {mix_oklab('#0070f3', '#000000', 1)}"))

    # oklab 压黑必须真的更暗（不是更亮）
    dark = shade("#0070f3", 8)
    lum = lambda h: sum(_srgb_to_linear(c) * w for c, w in
                        zip(_hex_to_rgb(h), (0.2126, 0.7152, 0.0722)))
    checks.append(("shade() 压黑方向正确", lum(dark) < lum("#0070f3"),
                   f"{dark} 亮度 {lum(dark):.4f} < #0070f3 亮度 {lum('#0070f3'):.4f}"))

    # 与浏览器 color-mix 已知结果对齐：Stripe 手工值 vs 我们的公式
    # （Stripe 的 hover 是手挑值，不作比对；用中性色做交叉验证）
    got = shade("#ffffff", 50)
    checks.append(("shade(#ffffff,50) 落在中灰区间",
                   0x60 <= int(got[1:3], 16) <= 0xa0, f"得到 {got}"))

    # 能力三层色阶：L1 最深 → L3 最浅，所以亮度必须严格递增（数字越大越亮）
    ok_ramp, detail = True, []
    for track in ("sci", "art", "biz"):
        tk = tokens_for(track)
        lums = [lum(tk[f"cap-l{i}"]) for i in (1, 2, 3)]
        detail.append(f"{track}:{lums[0]:.3f}<{lums[1]:.3f}<{lums[2]:.3f}")
        if not (lums[0] < lums[1] < lums[2]):
            ok_ramp = False
    checks.append(("能力三层色阶 L1→L3 亮度严格递增", ok_ramp, "  ".join(detail)))

    # 三个系统必须互不相同（避免复制粘贴错）
    slugs = {tokens_for(k)["_meta"]["slug"] for k in ("sci", "art", "biz")}
    checks.append(("三轨道映射到三套不同设计系统", len(slugs) == 3, ", ".join(sorted(slugs))))

    # 未知轨道回退
    checks.append(("未知轨道回退到 sci", system_for_track("nope") == "vercel",
                   system_for_track("nope")))

    # css_root 可产出且无遗留 _meta
    block, meta = css_root("sci")
    checks.append(("css_root 产出合法且无 _meta 泄漏",
                   "--bg:" in block and "_meta" not in block and meta["slug"] == "vercel",
                   f"{len(block.splitlines())} 行"))

    allok = True
    print("=== design_systems.py 自检 ===")
    for name, ok, info in checks:
        print(f"[{'✓' if ok else '✗'}] {name}" + (f"  -> {info}" if info else ""))
        allok = allok and ok
    print("\n" + ("[✓] 全部自检通过" if allok else "[✗] 存在失败项"))
    return 0 if allok else 1


if __name__ == "__main__":
    import sys
    sys.exit(selftest())

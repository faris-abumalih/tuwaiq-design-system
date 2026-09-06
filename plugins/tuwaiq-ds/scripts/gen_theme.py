#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""يولّد theme.css من tokens.json — لا تعدّل theme.css يدويًا أبدًا."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(HERE)
T = json.load(open(os.path.join(ROOT, "tokens", "tokens.json"), encoding="utf-8"))

def val(x):
    return x["value"] if isinstance(x, dict) else x

L = []
w = L.append
w("/* ─────────────────────────────────────────────────────────────────────────")
w("   Tuwaiq DS v%s — مولّد آليًا من tokens.json. لا تعدّله يدويًا." % T["$meta"]["version"])
w("   إعادة التوليد:  python3 scripts/gen_theme.py > src/styles/theme.css")
w("   ───────────────────────────────────────────────────────────────────────── */")
w("")
w("@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600&display=swap');")
w("")
w(":root {")
w("  /* ── الخط ── */")
w("  --font-family: %s;" % val(T["font"]["family"]))
for k, v in T["font"]["weight"].items():
    w("  --fw-%s: %s;" % (k, v))
w("")
w("  /* ── الألوان ── */")
for name, spec in T["color"].items():
    use = spec.get("use", "") if isinstance(spec, dict) else ""
    w("  --%s: %s;%s" % (name, val(spec), ("  /* %s */" % use) if use else ""))
w("")
w("  /* ── سلّم الطباعة (المقاس فقط — استخدم كلاسات .t-* للحزمة كاملة) ── */")
for name, spec in T["type"].items():
    w("  --text-%s: %dpx;" % (name, spec["size"]))
    w("  --lh-%s: %s;" % (name, spec["lh"]))
w("")
w("  /* ── المسافات ── */")
for n in T["space"]["scale"]:
    w("  --space-%d: %dpx;" % (n, n))
w("")
w("  /* ── الزوايا ── */")
for k, v in T["radius"].items():
    w("  --radius-%s: %dpx;" % (k, v))
w("")
w("  /* ── الظلال ── */")
for k, spec in T["shadow"].items():
    w("  --shadow-%s: %s;" % (k, val(spec)))
w("")
w("  /* ── الحركة ── */")
for k, spec in T["motion"].items():
    prefix = "--ease" if k == "ease" else "--dur-%s" % k
    w("  %s: %s;" % (prefix if k == "ease" else prefix, val(spec)))
w("")
w("  /* ── القياسات ── */")
for k, v in T["layout"].items():
    w("  --%s: %dpx;" % (k, v))
w("}")
w("")
w("/* ── سلّم الطباعة كصفوف جاهزة — استخدمها بدل fontSize اليدوي ── */")
for name, spec in T["type"].items():
    w(".t-%s { font-size: var(--text-%s); line-height: var(--lh-%s); font-weight: %d; }"
      % (name, name, name, spec["weight"]))
w("")
w("/* ── ربط التوكنز بـ Tailwind v4 ── */")
w("@theme inline {")
w("  --font-sans: var(--font-family);")
for name in T["color"]:
    w("  --color-%s: var(--%s);" % (name, name))
for k in T["radius"]:
    w("  --radius-%s: var(--radius-%s);" % (k, k))
w("}")
w("")
w("/* ── الأساس ── */")
w("html { font-family: var(--font-family); font-size: var(--text-body); }")
w("body { margin: 0; background: var(--bg); color: var(--text); line-height: var(--lh-body); }")
w("*, *::before, *::after { box-sizing: border-box; }")
w("::placeholder { color: var(--text-faint); }")
w(":focus-visible { outline: 2px solid var(--brand); outline-offset: 2px; }")
w("")
w("@media (prefers-reduced-motion: reduce) {")
w("  *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }")
w("}")

out = "\n".join(L) + "\n"
if len(sys.argv) > 1 and sys.argv[1] != "-":
    open(sys.argv[1], "w", encoding="utf-8").write(out)
    print("كُتب: %s" % sys.argv[1], file=sys.stderr)
else:
    sys.stdout.write(out)

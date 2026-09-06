#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اختبار ذاتي لمحرّك الفحص — python3 scripts/selftest.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_lint as D

CASES = [
    # (وصف, مسار, كود, قواعد متوقّعة كأخطاء, قواعد ممنوع أن تظهر)
    ("لون خام", "a.tsx", 'const s = { color: "#4931AF" };', ["no-raw-color"], []),
    ("rgba خام", "a.tsx", 'const s = { color: "rgba(0,0,0,.5)" };', ["no-raw-color"], []),
    ("توكن سليم", "a.tsx", 'const s = { color: "var(--brand)" };', [], ["no-raw-color"]),
    ("tailwind عشوائي", "a.tsx", '<div className="bg-[#eee]" />', ["no-raw-color"], []),
    ("مقاس خط شاذ", "a.tsx", 'const s = { fontSize: "13.5px" };', ["no-raw-font-size"], []),
    ("مقاس خط سليم", "a.tsx", 'const s = { fontSize: "14px" };', [], ["no-raw-font-size"]),
    ("زاوية شاذة", "a.tsx", 'const s = { borderRadius: 18 };', ["no-raw-radius"], []),
    ("زاوية سليمة", "a.tsx", 'const s = { borderRadius: 16 };', [], ["no-raw-radius"]),
    ("خاصية فيزيائية", "a.tsx", 'const s = { marginLeft: 8 };', ["rtl-logical-props"], []),
    ("خاصية منطقية", "a.tsx", 'const s = { marginInlineStart: 8 };', [], ["rtl-logical-props"]),
    ("كلاس اتجاهي", "a.tsx", '<div className="ml-2 text-left" />', ["rtl-logical-props"], []),
    ("كلاس منطقي", "a.tsx", '<div className="ms-2 text-start" />', [], ["rtl-logical-props"]),
    ("توسيط left 50%", "a.tsx", 'const s = { position: "absolute", left: "50%" };', [], ["rtl-logical-props"]),
    ("نوع TS اسمه left", "a.tsx", 'type P = { left: number };', [], ["rtl-logical-props"]),
    ("زر خام", "a.tsx", '<button onClick={go} />', ["no-raw-element"], []),
    ("زر داخل primitives", "src/components/primitives/b.tsx", '<button />', [], ["no-raw-element"]),
    ("نص عربي في الكود", "a.tsx", '<h1>الفعاليات</h1>', ["i18n-hardcoded-text"], []),
    ("نص عربي في تعليق", "a.tsx", '// عنوان الصفحة\nconst x = 1;', [], ["i18n-hardcoded-text"]),
    ("نص عربي في JSX comment", "a.tsx", '{/* شرح للمطوّر */}', [], ["i18n-hardcoded-text"]),
    ("i18n سليم", "a.tsx", '<h1>{t("events.title")}</h1>', [], ["i18n-hardcoded-text"]),
    ("خط يدوي", "a.tsx", 'const s = { fontFamily: "Arial" };', ["no-hardcoded-font"], []),
    ("ظل بتوكن", "a.tsx", 'const s = { boxShadow: "var(--shadow-2)" };', [], ["off-token-shadow"]),
    ("theme.css معفى", "src/styles/theme.css", ':root { --brand: #4931AF; }', [], ["no-raw-color"]),
    ("استثناء بسبب", "a.tsx", 'const c = "#FF00AA"; // ds-allow: no-raw-color — لون منصة خارجية', [], ["no-raw-color"]),
    ("استثناء بلا سبب", "a.tsx", 'const c = "#FF00AA"; // ds-allow', ["no-raw-color"], []),
    ("CSS فيزيائي", "a.css", '.x { margin-left: 8px; }', ["rtl-logical-props"], []),
    ("CSS منطقي", "a.css", '.x { margin-inline-start: 8px; }', [], ["rtl-logical-props"]),
    ("حقل وقت أصلي", "src/components/primitives/f.tsx", '<input type="time" />', [], ["no-raw-element"]),
    ("نموذج بلا طي", "a.tsx", "\n".join(['<Field />'] * 8), [], []),
    ("نموذج مع طي", "a.tsx", "\n".join(['<Field />'] * 8 + ['<AdvancedSection />']), [], ["unfolded-form"]),
]

WARN_CASES = [
    ("تحذير: حقل وقت أصلي", "src/components/primitives/f.tsx", '<input type="time" />', ["native-datetime"]),
    ("تحذير: نموذج بلا طي", "a.tsx", "\n".join(['<Field />'] * 8), ["unfolded-form"]),
]

def run():
    passed = failed = 0
    for desc, path, code, want, forbid in CASES:
        fs = D.lint(path, code, fragment=False, cfg=D.DEFAULT_CONFIG)
        errs = {f.rule for f in fs if f.severity == "error"}
        all_rules = {f.rule for f in fs}
        missing = [r for r in want if r not in errs]
        extra = [r for r in forbid if r in all_rules]
        if missing or extra:
            failed += 1
            print("✗ %s" % desc)
            if missing: print("    ناقص: %s (وجدنا: %s)" % (missing, sorted(all_rules) or "لا شيء"))
            if extra:   print("    زائد: %s" % extra)
        else:
            passed += 1
    for desc, path, code, want in WARN_CASES:
        rules = {f.rule for f in D.lint(path, code, fragment=False, cfg=D.DEFAULT_CONFIG)
                 if f.severity == "warning"}
        if all(r in rules for r in want):
            passed += 1
        else:
            failed += 1
            print("✗ %s — ناقص %s (وجدنا %s)" % (desc, want, sorted(rules) or "لا شيء"))

    print("\n%d نجح · %d فشل" % (passed, failed))
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(run())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tuwaiq DS — محرّك الفحص الإلزامي للنظام التصميمي.

ثلاثة أوضاع:
  --hook-pre    هوك PreToolUse: يقرأ JSON من stdin ويمنع الكتابة إذا فيها مخالفة (error).
  --hook-post   هوك PostToolUse: يفحص الملف كاملًا بعد الكتابة ويبلّغ Claude بالتحذيرات.
  <paths...>    وضع CLI (للـ CI): يفحص ملفات/مجلدات ويرجع exit 1 عند وجود أخطاء.

بدون أي اعتماديات خارجية — stdlib فقط.
"""
import sys, os, re, json, fnmatch

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(HERE)
TOKENS_PATH = os.path.join(PLUGIN_ROOT, "tokens", "tokens.json")

# ── تحميل التوكنز (المصدر الوحيد للحقيقة) ────────────────────────────────────
def load_tokens():
    try:
        with open(TOKENS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

TOKENS = load_tokens()

def _hex_map():
    m = {}
    for name, spec in (TOKENS.get("color") or {}).items():
        v = spec.get("value", "") if isinstance(spec, dict) else str(spec)
        key = v.lower().replace(" ", "")
        if key in m and not m[key].startswith("chart-"):
            continue          # أول توكن دلالي يفوز على chart-*
        m[key] = name
    return m

HEX_TO_TOKEN   = _hex_map()
TYPE_SIZES     = sorted({int(t["size"]) for t in (TOKENS.get("type") or {}).values()}) or [12,13,14,15,16,20,28]
TYPE_BY_SIZE   = {int(t["size"]): n for n, t in (TOKENS.get("type") or {}).items()}
SPACE_SCALE    = set((TOKENS.get("space") or {}).get("scale") or [2,4,6,8,12,16,20,24,32,40,48,64])
RADIUS_SCALE   = {int(v): k for k, v in (TOKENS.get("radius") or {}).items()}
if not RADIUS_SCALE:
    RADIUS_SCALE = {8:"sm",12:"md",16:"lg",20:"xl",24:"2xl",9999:"full"}

# ── الإعدادات القابلة للتخصيص في المشروع (ds.config.json) ────────────────────
DEFAULT_CONFIG = {
    "include":        ["**/*.tsx", "**/*.jsx", "**/*.ts", "**/*.js", "**/*.css"],
    "ignore":         ["**/node_modules/**", "**/dist/**", "**/build/**", "**/.next/**",
                       "**/coverage/**", "**/*.test.*", "**/*.spec.*", "**/*.d.ts",
                       "**/vite.config.*", "**/eslint.config.*", "**/tailwind.config.*"],
    # الملفات المسموح لها تعريف قيم خام (هي مصدر التوكنز نفسه)
    "tokenFiles":     ["**/theme.css", "**/tokens.css", "**/ds-tokens.*", "**/tokens.json"],
    # مجلدات الـ primitives: مسموح فيها عناصر HTML الخام لأنها هي اللي تغلّفها
    "primitivesDirs": ["**/components/primitives/**", "**/components/ui/**", "**/ds/**",
                       "**/assets/primitives/**"],
    "rules":          {}
}

def find_project_config(start_path):
    d = os.path.abspath(start_path if os.path.isdir(start_path) else os.path.dirname(start_path))
    for _ in range(12):
        c = os.path.join(d, "ds.config.json")
        if os.path.isfile(c):
            try:
                with open(c, encoding="utf-8") as f:
                    user = json.load(f)
                cfg = dict(DEFAULT_CONFIG)
                cfg.update({k: v for k, v in user.items() if k != "rules"})
                cfg["rules"] = dict(user.get("rules") or {})
                return cfg
            except Exception:
                break
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return dict(DEFAULT_CONFIG)

def matches_any(path, patterns):
    p = path.replace(os.sep, "/")
    return any(fnmatch.fnmatch(p, pat) or fnmatch.fnmatch(os.path.basename(p), pat) for pat in patterns)

# ── نموذج المخالفة ───────────────────────────────────────────────────────────
class Finding:
    __slots__ = ("line", "rule", "severity", "message", "fix")
    def __init__(self, line, rule, severity, message, fix=""):
        self.line, self.rule, self.severity, self.message, self.fix = line, rule, severity, message, fix

ARABIC = re.compile(r"[؀-ۿ]")
ALLOW  = re.compile(r"ds-allow\s*:?\s*([a-z0-9\-]+)?\s*(.*)$", re.I)

def allowed(lines, idx, rule):
    """السماح باستثناء صريح على نفس السطر أو السطر السابق — بشرط ذكر سبب."""
    for i in (idx, idx - 1):
        if i < 0:
            continue
        m = ALLOW.search(lines[i])
        if not m:
            continue
        named, reason = (m.group(1) or "").lower(), (m.group(2) or "").strip(" -—*/")
        if named and named != rule:
            continue
        if len(reason) >= 4:      # لازم سبب مكتوب، مو مجرد إسكات
            return True
    return False

RE_LINE_COMMENT = re.compile(r"(?<!:)//.*$")

def code_only(lines):
    """يرجع نسخة من الأسطر بدون التعليقات — عشان ما نبلّغ عن مخالفات داخل شرح مكتوب."""
    out, in_block = [], False
    for raw in lines:
        line, res = raw, []
        while line:
            if in_block:
                end = line.find("*/")
                if end == -1:
                    line = ""
                    break
                line, in_block = line[end + 2:], False
                continue
            start = line.find("/*")
            if start == -1:
                res.append(RE_LINE_COMMENT.sub("", line))
                break
            res.append(line[:start])
            line, in_block = line[start + 2:], True
        joined = "".join(res)
        # تنظيف بقايا فتحة JSX comment «{» اليتيمة
        out.append(joined)
    return out

# ── القواعد ──────────────────────────────────────────────────────────────────
RE_HEX        = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RE_FUNC_COLOR = re.compile(r"\b(?:rgba?|hsla?)\(\s*[\d.]+")
RE_TW_COLOR   = re.compile(r"\b(?:bg|text|border|from|to|via|fill|stroke|ring|shadow|decoration|outline|accent|caret|divide)-\[\s*(?:#|rgb|hsl)")
RE_RADIUS_JS  = re.compile(r"borderRadius\s*:\s*[\"']?([\d.]+)(?:px)?[\"']?")
RE_RADIUS_CSS = re.compile(r"border-radius\s*:\s*([\d.]+)px")
RE_RADIUS_TW  = re.compile(r"\brounded(?:-[a-z]+)?-\[[^\]]+\]")
RE_RADIUS_PCT = re.compile(r"border-?[Rr]adius\s*:\s*[\"']?50%")
RE_FS_JS      = re.compile(r"fontSize\s*:\s*[\"']?([\d.]+)px")
RE_FS_CSS     = re.compile(r"font-size\s*:\s*([\d.]+)px")
RE_FS_TW      = re.compile(r"\btext-\[\s*([\d.]+)px\s*\]")
RE_SPACE_JS   = re.compile(r"\b(padding|margin|gap|rowGap|columnGap|paddingInline|paddingBlock|marginInline|marginBlock|paddingTop|paddingBottom|marginTop|marginBottom|paddingInlineStart|paddingInlineEnd|marginInlineStart|marginInlineEnd)\s*:\s*[\"']?([\d.]+)px")
RE_FONT_FAM   = re.compile(r"font-?[Ff]amily\s*:\s*[\"'][^\"']*[\"']")
RE_SHADOW     = re.compile(r"\bbox-?[Ss]hadow\s*:\s*[\"']?\s*([^\"';,}]+)")
RE_DIR_RTL    = re.compile(r"""(?<!\[)\bdir\s*=\s*["']rtl["']""")
RE_RAW_EL     = re.compile(r"<(button|input|select|textarea|table|dialog)\b")
RE_NATIVE_DT  = re.compile(r"""type\s*=\s*["']?(date|time|datetime-local)["']?""")
RE_FIELDISH   = re.compile(r"<(?:Field|Input|TextArea|Textarea|Select|input|textarea|select)\b")
RE_FOLDED     = re.compile(r"advanced|collaps|accordion|disclosure|<details|moreOptions|expandable", re.I)

PHYSICAL_JS = {
    "marginLeft": "marginInlineStart", "marginRight": "marginInlineEnd",
    "paddingLeft": "paddingInlineStart", "paddingRight": "paddingInlineEnd",
    "borderLeft": "borderInlineStart", "borderRight": "borderInlineEnd",
    "borderLeftWidth": "borderInlineStartWidth", "borderRightWidth": "borderInlineEndWidth",
    "borderLeftColor": "borderInlineStartColor", "borderRightColor": "borderInlineEndColor",
    "borderTopLeftRadius": "borderStartStartRadius", "borderTopRightRadius": "borderStartEndRadius",
    "borderBottomLeftRadius": "borderEndStartRadius", "borderBottomRightRadius": "borderEndEndRadius",
    "left": "insetInlineStart", "right": "insetInlineEnd",
}
PHYSICAL_CSS = {
    "margin-left": "margin-inline-start", "margin-right": "margin-inline-end",
    "padding-left": "padding-inline-start", "padding-right": "padding-inline-end",
    "border-left": "border-inline-start", "border-right": "border-inline-end",
    "left": "inset-inline-start", "right": "inset-inline-end",
}
RE_PHYS_JS   = re.compile(r"(?<![A-Za-z])(" + "|".join(sorted(PHYSICAL_JS, key=len, reverse=True)) + r")\s*:")
RE_PHYS_CSS  = re.compile(r"(?<![-\w])(" + "|".join(sorted(PHYSICAL_CSS, key=len, reverse=True)) + r")\s*:")
RE_TEXT_ALIGN= re.compile(r"""text-?[Aa]lign\s*:\s*["']?(left|right)\b""")
RE_TW_PHYS   = re.compile(r"""(?<![\w-])(?:ml|mr|pl|pr|left|right|border-l|border-r|rounded-l|rounded-r)-(?:\[[^\]]+\]|[\w.\/]+)""")
RE_TW_ALIGN  = re.compile(r"(?<![\w-])text-(?:left|right)(?![\w-])")
TW_LOGICAL   = {"ml":"ms","mr":"me","pl":"ps","pr":"pe","left":"start","right":"end",
                "border-l":"border-s","border-r":"border-e","rounded-l":"rounded-s","rounded-r":"rounded-e"}


def color_fix(raw):
    tok = HEX_TO_TOKEN.get(raw.lower())
    if tok:
        return "استبدله بـ var(--%s)" % tok
    return "ما فيه توكن بهذي القيمة — استخدم أقرب توكن، أو أضِف توكن جديد في tokens.json عبر PR"


def lint(path, text, fragment=False, cfg=None):
    cfg = cfg or DEFAULT_CONFIG
    rules_cfg = cfg.get("rules", {})
    ext = os.path.splitext(path)[1].lower()
    is_css = ext == ".css"
    is_code = ext in (".tsx", ".jsx", ".ts", ".js")
    is_token_file = matches_any(path, cfg.get("tokenFiles", []))
    is_primitive = matches_any(path, cfg.get("primitivesDirs", []))
    lines = text.splitlines()
    out = []

    def add(i, rule, sev, msg, fix=""):
        sev = rules_cfg.get(rule, sev)
        if sev == "off" or allowed(lines, i, rule):
            return
        out.append(Finding(i + 1, rule, sev, msg, fix))

    if "ds-exempt-file" in "\n".join(lines[:5]):
        return out

    for i, line in enumerate(code_only(lines)):
        if not line.strip():
            continue

        # 1) ألوان خام
        if not is_token_file:
            for m in RE_HEX.finditer(line):
                add(i, "no-raw-color", "error",
                    "لون خام %s — الألوان تجي من التوكنز فقط." % m.group(0), color_fix(m.group(0)))
            for m in RE_FUNC_COLOR.finditer(line):
                seg = line[m.start():m.start() + 40]
                if re.match(r"\brgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0\s*\)", seg):
                    continue
                add(i, "no-raw-color", "error",
                    "لون خام %s… — استخدم توكن." % seg.split(")")[0][:28],
                    "var(--text-muted) / var(--hairline) / var(--surface-2) حسب الاستخدام")
            if RE_TW_COLOR.search(line):
                add(i, "no-raw-color", "error",
                    "كلاس Tailwind بلون عشوائي — ممنوع.",
                    "استخدم كلاسات التوكنز: bg-surface / text-muted / border-hairline …")

        # 2) الزوايا
        for m in (RE_RADIUS_JS.finditer(line) if is_code else RE_RADIUS_CSS.finditer(line)):
            try: v = int(float(m.group(1)))
            except Exception: continue
            if v not in RADIUS_SCALE:
                near = min(RADIUS_SCALE, key=lambda k: abs(k - v))
                add(i, "no-raw-radius", "error",
                    "زاوية %dpx خارج سلّم النظام." % v,
                    "استخدم var(--radius-%s)%s" % (RADIUS_SCALE[near],
                        " (الأقرب %dpx)" % near if near != 9999 else " (دائري كامل)"))
        if RE_RADIUS_TW.search(line):
            add(i, "no-raw-radius", "error", "rounded بقيمة عشوائية.", "استخدم rounded-md / lg / xl / full")
        if RE_RADIUS_PCT.search(line):
            add(i, "no-raw-radius", "error", "borderRadius: 50% غير موحّد.", "استخدم var(--radius-full)")

        # 3) مقاسات الخط
        for m in (RE_FS_JS.finditer(line) if is_code else RE_FS_CSS.finditer(line)):
            v = float(m.group(1))
            if int(v) != v or int(v) not in TYPE_SIZES:
                near = min(TYPE_SIZES, key=lambda k: abs(k - v))
                add(i, "no-raw-font-size", "error",
                    "مقاس خط %spx خارج سلّم الطباعة." % (int(v) if v == int(v) else v),
                    "استخدم var(--text-%s) = %dpx" % (TYPE_BY_SIZE.get(near, "body"), near))
        for m in RE_FS_TW.finditer(line):
            add(i, "no-raw-font-size", "error", "text-[%spx] عشوائي." % m.group(1),
                "استخدم كلاس من سلّم الطباعة")

        # 4) المسافات
        if is_code:
            for m in RE_SPACE_JS.finditer(line):
                v = float(m.group(2))
                if int(v) != v or int(v) not in SPACE_SCALE:
                    near = min(SPACE_SCALE, key=lambda k: abs(k - v))
                    add(i, "off-scale-spacing", "warning",
                        "%s: %spx خارج سلّم المسافات." % (m.group(1), m.group(2)),
                        "الأقرب في السلّم: %dpx" % near)

        # 5) RTL — الخصائص الفيزيائية ممنوعة
        for m in RE_PHYS_JS.finditer(line) if is_code else []:
            k = m.group(1)
            sev = "error"
            if k in ("left", "right"):
                rest = line[m.end():]
                if re.match(r'\s*(number|string|boolean)\b', rest):
                    continue      # تعريف نوع TypeScript، مو ستايل
                if re.match(r'\s*["\']?50%', rest):
                    continue      # نمط التوسيط left:50% + translateX(-50%) محايد اتجاهيًا
                if not re.match(r'\s*["\']?-?[\d.]+\s*(px|rem|em|%)?["\']?\s*[,}\)]', rest):
                    sev = "warning"   # قيمة محسوبة (بورتال/قياس) — تنبيه لا حجب
            add(i, "rtl-logical-props", sev,
                "«%s» خاصية فيزيائية تكسر الواجهة العربية." % k,
                "استخدم %s%s" % (PHYSICAL_JS[k],
                    " — إلا إذا كانت إحداثية محسوبة من getBoundingClientRect، وقتها وثّقها بـ ds-allow" if sev == "warning" else ""))
        for m in RE_PHYS_CSS.finditer(line) if is_css else []:
            k = m.group(1)
            add(i, "rtl-logical-props", "error",
                "«%s» خاصية فيزيائية تكسر RTL." % k, "استخدم %s" % PHYSICAL_CSS[k])
        for m in RE_TEXT_ALIGN.finditer(line):
            add(i, "rtl-logical-props", "error",
                "text-align: %s ثابت." % m.group(1),
                "استخدم %s" % ("start" if m.group(1) == "left" else "end"))
        for m in RE_TW_PHYS.finditer(line):
            head = m.group(0).split("-")[0] if m.group(0).split("-")[0] in TW_LOGICAL else "-".join(m.group(0).split("-")[:2])
            add(i, "rtl-logical-props", "error",
                "كلاس اتجاهي ثابت «%s»." % m.group(0),
                "استخدم %s-*" % TW_LOGICAL.get(head, "المنطقي المقابل"))
        if RE_TW_ALIGN.search(line):
            add(i, "rtl-logical-props", "error", "text-left/right ثابت.", "استخدم text-start / text-end")

        # 6) عناصر HTML خام بدل مكوّنات النظام
        if is_code and not is_primitive:
            m = RE_RAW_EL.search(line)
            if m:
                el = m.group(1)
                repl = {"button": "<TuwayqButton>", "input": "<Field>/<SearchInput>",
                        "select": "<Select> أو Popover باختيارات بصرية", "textarea": "<Field multiline>",
                        "table": "<TuwayqTable>", "dialog": "<Modal> / <SideSheet>"}[el]
                add(i, "no-raw-element", "error",
                    "<%s> خام خارج مجلد الـ primitives." % el,
                    "استخدم %s من النظام" % repl)

        # 6ب) حقول التاريخ/الوقت الأصلية بدل لحظات النظام
        if is_code and RE_NATIVE_DT.search(line):
            add(i, "native-datetime", "warning",
                "حقل تاريخ/وقت أصلي — بارد ولا يتّسق مع النظام.",
                "شريط أيام أفقي للتاريخ، وستيبر «− 8:00 ص +» في بوبوفر للوقت "
                "(references/design-thinking.md — القرار ٦)")

        # 7) نص عربي مكتوب في الكود بدل i18n
        if ext in (".tsx", ".jsx") and ARABIC.search(line):
            add(i, "i18n-hardcoded-text", "error",
                "نص عربي مكتوب مباشرة في الكود.",
                "انقله إلى locales/ar/translation.json واستدعِ t('...')")

        # 8) خط ثابت
        if RE_FONT_FAM.search(line) and "var(" not in line and not is_token_file:
            add(i, "no-hardcoded-font", "error", "خط مكتوب يدويًا.", "استخدم var(--font-family)")

        # 9) ظلال عشوائية
        ms = RE_SHADOW.search(line)
        if ms and not is_token_file and not ms.group(1).lstrip().startswith(("var(", "none", "inherit", "0 0 0 0")):
            add(i, "off-token-shadow", "warning", "ظل خارج التوكنز.",
                "استخدم var(--shadow-1|2|3) — والأفضل مسافة بدل الظل (مبدأ ٥)")

        # 10) اتجاه ثابت
        if RE_DIR_RTL.search(line):
            add(i, "hardcoded-dir", "warning",
                'dir="rtl" ثابت.',
                'خلّه يتبع لغة التطبيق (i18n dir) — و dir="ltr" فقط للأرقام/الروابط/الرسوم')

    # قواعد على مستوى الملف (ما تنطبق على الشظايا)
    if not fragment and ext in (".tsx", ".jsx"):
        code = "\n".join(code_only(lines))
        n_fields = len(RE_FIELDISH.findall(code))
        if n_fields >= 7 and not RE_FOLDED.search(code):
            out.append(Finding(1, "unfolded-form", "warning",
                "%d حقلًا في شاشة واحدة بلا أي طي." % n_fields,
                "اسأل لكل حقل: هل يمنع غيابه إنشاء الكيان؟ لا → «خيارات متقدمة» أو صفحة الإعدادات. "
                "علامة * على المطلوب ليست بديلًا عن الطي (references/design-thinking.md — القرار ٣)"))

    if not fragment and is_css and ("@keyframes" in text or re.search(r"\banimation\s*:", text)):
        if "prefers-reduced-motion" not in text:
            out.append(Finding(1, "reduced-motion", "warning",
                "الملف فيه حركة بدون احترام prefers-reduced-motion.",
                "أضِف @media (prefers-reduced-motion: reduce) { animation: none }"))
    return out


# ── التنسيق والإخراج ─────────────────────────────────────────────────────────
def fmt(path, findings, color=True):
    E, W, R, B = ("\033[31m", "\033[33m", "\033[0m", "\033[1m") if color else ("", "", "", "")
    rel = path
    out = []
    for f in findings:
        tag = ("%sخطأ%s" % (E, R)) if f.severity == "error" else ("%sتنبيه%s" % (W, R))
        out.append("  %s:%d  %s  [%s] %s" % (rel, f.line, tag, f.rule, f.message))
        if f.fix:
            out.append("        ↳ %s" % f.fix)
    return "\n".join(out)


def collect(paths, cfg):
    files = []
    for p in paths:
        if os.path.isfile(p):
            files.append(p)
        else:
            for root, dirs, names in os.walk(p):
                dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "dist", "build", ".next", "coverage")]
                for n in names:
                    fp = os.path.join(root, n)
                    if matches_any(fp, cfg["include"]) and not matches_any(fp, cfg["ignore"]):
                        files.append(fp)
    return files


def lintable(path, cfg):
    return matches_any(path, cfg["include"]) and not matches_any(path, cfg["ignore"])


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


# ── الأوضاع ──────────────────────────────────────────────────────────────────
def hook_input():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def extract(payload):
    """يرجع (file_path, [(نص, هل هو شظية)])"""
    ti = payload.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("path") or ""
    name = payload.get("tool_name") or ""
    chunks = []
    if name == "Write":
        chunks.append((ti.get("content") or ti.get("file_text") or "", False))
    elif name == "Edit":
        chunks.append((ti.get("new_string") or "", True))
    elif name in ("MultiEdit", "NotebookEdit"):
        for e in (ti.get("edits") or []):
            chunks.append((e.get("new_string") or "", True))
    return path, chunks


def mode_pre():
    if os.environ.get("DS_LINT_OFF") == "1":
        return 0
    payload = hook_input()
    path, chunks = extract(payload)
    if not path or not chunks:
        return 0
    cfg = find_project_config(payload.get("cwd") or path)
    if not lintable(path, cfg):
        return 0
    findings = []
    for text, frag in chunks:
        findings += [f for f in lint(path, text, fragment=frag, cfg=cfg) if f.severity == "error"]
    if not findings:
        return 0
    body = fmt(os.path.basename(path), findings, color=False)
    reason = (
        "⛔ الكتابة مرفوضة — الكود يخالف نظام تويق التصميمي (%d مخالفة):\n%s\n\n"
        "صحّح المخالفات وأعد المحاولة. راجع مهارة tuwaiq-ds (references/tokens.md).\n"
        "استثناء مشروع (نادر): أضف تعليق `ds-allow: <rule> — السبب` على السطر نفسه أو قبله."
        % (len(findings), body)
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }, ensure_ascii=False))
    return 0


def mode_post():
    if os.environ.get("DS_LINT_OFF") == "1":
        return 0
    payload = hook_input()
    ti = payload.get("tool_input") or {}
    path = ti.get("file_path") or ""
    cfg = find_project_config(payload.get("cwd") or path or ".")
    if not path or not os.path.isfile(path) or not lintable(path, cfg):
        return 0
    findings = lint(path, read(path), fragment=False, cfg=cfg)
    if not findings:
        return 0
    errs = [f for f in findings if f.severity == "error"]
    body = fmt(os.path.basename(path), findings, color=False)
    sys.stderr.write("فحص نظام تويق التصميمي — %d خطأ / %d تنبيه:\n%s\n" % (len(errs), len(findings) - len(errs), body))
    return 2 if errs else 0


def mode_cli(argv):
    strict = "--strict" in argv
    as_json = "--json" in argv
    paths = [a for a in argv if not a.startswith("-")] or ["."]
    cfg = find_project_config(paths[0])
    files = collect(paths, cfg)
    total_e = total_w = 0
    blocks, records = [], []
    for fp in sorted(files):
        fs = lint(fp, read(fp), fragment=False, cfg=cfg)
        if not fs:
            continue
        total_e += sum(1 for f in fs if f.severity == "error")
        total_w += sum(1 for f in fs if f.severity == "warning")
        blocks.append(fmt(os.path.relpath(fp), fs, color=sys.stdout.isatty()))
        records += [{"file": os.path.relpath(fp), "line": f.line, "rule": f.rule,
                     "severity": f.severity, "message": f.message, "fix": f.fix} for f in fs]
    if as_json:
        print(json.dumps({"errors": total_e, "warnings": total_w, "findings": records},
                         ensure_ascii=False, indent=2))
    else:
        if blocks:
            print("\n".join(blocks))
        print("\nنظام تويق التصميمي: %d ملف مفحوص — %d خطأ، %d تنبيه." % (len(files), total_e, total_w))
        if total_e == 0 and total_w == 0:
            print("✅ مطابق للنظام بالكامل.")
    return 1 if (total_e or (strict and total_w)) else 0


SESSION_BRIEF = """<tuwaiq-ds>
نظام تويق التصميمي مفعّل على هذا المشروع. الالتزام إلزامي ومفحوص آليًا قبل كل كتابة ملف.

القواعد الصلبة (أي مخالفة = رفض الكتابة):
1. ما فيه لون/مقاس خط/زاوية مكتوب يدويًا — كله var(--token). التوكنز: {tokens}
2. ممنوع الخصائص الاتجاهية الفيزيائية (marginLeft, text-left, ml-*, pl-*) — المنطقية فقط (marginInlineStart, text-start, ms-*, ps-*).
3. ممنوع <button>/<input>/<table> خام — استخدم مكوّنات النظام.
4. ممنوع نص عربي داخل الكود — t() و locales فقط.
5. المسافات من السلّم: 2/4/6/8/12/16/20/24/32/40/48/64.

وقبل أي شاشة — إلزامي — بطاقة القرارات الستة (references/design-thinking.md):
الحاوية حسب وزن الإجراء في المنتج لا عدد حقوله · بطل واحد بمقاس العنوان · ما لا يمنع غيابه
الإنشاء يُطوى أو يُؤجّل (وعلامة * ليست بديلًا عن الطي) · شكل كل اختيار حسب طبيعته ·
الإدخال داخل المعاينة لما يكون شكل الشيء هو وظيفته · لحظة ممتعة أو اثنتان لا أكثر.

قبل بناء أي صفحة أو مكوّن: استدعِ مهارة tuwaiq-ds واتبع مسار العمل فيها.
فحص يدوي: python3 "{script}" src
</tuwaiq-ds>"""


def looks_like_ds_project(cwd):
    for probe in ("ds.config.json", "src/styles/theme.css", "package.json"):
        if os.path.isfile(os.path.join(cwd, probe)):
            return True
    return False


def mode_session():
    payload = hook_input()
    cwd = payload.get("cwd") or os.getcwd()
    if not looks_like_ds_project(cwd):
        return 0
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": SESSION_BRIEF.format(
                tokens=TOKENS_PATH, script=os.path.abspath(__file__))
        }
    }, ensure_ascii=False))
    return 0


def main():
    argv = sys.argv[1:]
    if "--hook-session" in argv:
        return mode_session()
    if "--hook-pre" in argv:
        return mode_pre()
    if "--hook-post" in argv:
        return mode_post()
    return mode_cli(argv)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:            # الهوك ما يعطّل الشغل أبدًا لو انكسر
        if "--hook" in " ".join(sys.argv):
            sys.stderr.write("ds_lint internal error: %s\n" % e)
            sys.exit(0)
        raise

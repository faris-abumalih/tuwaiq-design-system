#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# مثبّت نظام تويق التصميمي — بدون أي اعتماديات (bash + python3 فقط).
# يركّب المهارة والأمر والوكيل والهوكس في ~/.claude مباشرة.
#
#   التركيب/التحديث:   ./install.sh
#   الإزالة:           ./install.sh --uninstall
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_URL="https://github.com/faris-abumalih/tuwaiq-design-system.git"
CLAUDE_DIR="$HOME/.claude"
PAYLOAD="$CLAUDE_DIR/tuwaiq-ds"
SETTINGS="$CLAUDE_DIR/settings.json"
PY="$(command -v python3 || echo /usr/bin/python3)"

say() { printf '%s\n' "$*"; }

# ── الإزالة ──────────────────────────────────────────────────────────────────
if [ "${1:-}" = "--uninstall" ]; then
  rm -rf "$PAYLOAD" "$CLAUDE_DIR/skills/tuwaiq-ds" \
         "$CLAUDE_DIR/commands/ds.md" "$CLAUDE_DIR/agents/ds-reviewer.md"
  [ -f "$SETTINGS" ] && "$PY" - "$SETTINGS" <<'PYE'
import json, sys
p = sys.argv[1]
try:
    cfg = json.load(open(p, encoding="utf-8"))
except Exception:
    sys.exit(0)
hooks = cfg.get("hooks", {})
for ev in list(hooks):
    kept = []
    for entry in hooks[ev]:
        entry["hooks"] = [h for h in entry.get("hooks", []) if "ds_lint.py" not in str(h.get("command", ""))]
        if entry["hooks"]:
            kept.append(entry)
    if kept:
        hooks[ev] = kept
    else:
        del hooks[ev]
if hooks:
    cfg["hooks"] = hooks
else:
    cfg.pop("hooks", None)
json.dump(cfg, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PYE
  say "✓ أُزيل نظام تويق التصميمي."
  exit 0
fi

# ── مصدر الملفات: نسخة محلية أو استنساخ ─────────────────────────────────────
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SELF_DIR/plugins/tuwaiq-ds" ]; then
  SRC="$SELF_DIR/plugins/tuwaiq-ds"
else
  TMP="$(mktemp -d)"
  say "… استنساخ النظام"
  git clone --depth 1 --quiet "$REPO_URL" "$TMP/repo"
  SRC="$TMP/repo/plugins/tuwaiq-ds"
fi

# ── نسخ الحمولة ──────────────────────────────────────────────────────────────
rm -rf "$PAYLOAD"
mkdir -p "$PAYLOAD" "$CLAUDE_DIR/skills" "$CLAUDE_DIR/commands" "$CLAUDE_DIR/agents"
cp -R "$SRC/tokens" "$SRC/scripts" "$PAYLOAD/"
cp -R "$SRC/skills/tuwaiq-ds/assets" "$PAYLOAD/"
chmod +x "$PAYLOAD/scripts/"*.py

# ── المهارة والأمر والوكيل، مع استبدال مسار الحمولة ─────────────────────────
rm -rf "$CLAUDE_DIR/skills/tuwaiq-ds"
cp -R "$SRC/skills/tuwaiq-ds" "$CLAUDE_DIR/skills/tuwaiq-ds"
cp "$SRC/commands/ds.md"        "$CLAUDE_DIR/commands/ds.md"
cp "$SRC/agents/ds-reviewer.md" "$CLAUDE_DIR/agents/ds-reviewer.md"

"$PY" - "$CLAUDE_DIR" "$PAYLOAD" <<'PYE'
import os, sys
root, payload = sys.argv[1], sys.argv[2]
targets = [os.path.join(root, "commands", "ds.md"),
           os.path.join(root, "agents", "ds-reviewer.md")]
for d, _, fs in os.walk(os.path.join(root, "skills", "tuwaiq-ds")):
    targets += [os.path.join(d, f) for f in fs if f.endswith(".md")]
n = 0
for t in targets:
    try:
        s = open(t, encoding="utf-8").read()
    except Exception:
        continue
    new = s.replace("${CLAUDE_PLUGIN_ROOT}", payload).replace("$CLAUDE_PLUGIN_ROOT", payload)
    if new != s:
        open(t, "w", encoding="utf-8").write(new)
        n += 1
print("  استُبدل مسار النظام في %d ملف" % n)
PYE

# ── الهوكس ───────────────────────────────────────────────────────────────────
[ -f "$SETTINGS" ] && cp "$SETTINGS" "$SETTINGS.bak.$(date +%Y%m%d%H%M%S)"
"$PY" - "$SETTINGS" "$PAYLOAD" <<'PYE'
import json, os, sys
path, payload = sys.argv[1], sys.argv[2]
script = os.path.join(payload, "scripts", "ds_lint.py")
try:
    cfg = json.load(open(path, encoding="utf-8"))
except Exception:
    cfg = {}
hooks = cfg.get("hooks", {})

def clean(ev):
    kept = []
    for entry in hooks.get(ev, []):
        entry["hooks"] = [h for h in entry.get("hooks", []) if "ds_lint.py" not in str(h.get("command", ""))]
        if entry["hooks"]:
            kept.append(entry)
    return kept

def cmd(flag):
    return {"type": "command", "command": 'python3 "%s" %s' % (script, flag), "timeout": 15}

hooks["PreToolUse"]  = clean("PreToolUse")  + [{"matcher": "Write|Edit|MultiEdit", "hooks": [cmd("--hook-pre")]}]
hooks["PostToolUse"] = clean("PostToolUse") + [{"matcher": "Write|Edit|MultiEdit", "hooks": [cmd("--hook-post")]}]
hooks["SessionStart"] = clean("SessionStart") + [{"hooks": [cmd("--hook-session")]}]
cfg["hooks"] = hooks
os.makedirs(os.path.dirname(path), exist_ok=True)
json.dump(cfg, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("  الهوكس مضبوطة في settings.json")
PYE

# ── تحقّق ────────────────────────────────────────────────────────────────────
"$PY" "$PAYLOAD/scripts/selftest.py" >/dev/null && say "  الفحص الذاتي ✓"

if [ -d "$CLAUDE_DIR/skills/tuwaiq-design" ]; then
  say ""
  say "⚠︎  عندك مهارة قديمة: ~/.claude/skills/tuwaiq-design"
  say "   ألوانها تخالف النظام الموحّد. احذفها يدويًا لتفادي التعارض:"
  say "   rm -rf ~/.claude/skills/tuwaiq-design"
fi

say ""
say "✓ تم تركيب نظام تويق التصميمي."
say "  افتح جلسة جديدة واكتب:  /ds <طلبك>"
say "  للإزالة:  $SELF_DIR/install.sh --uninstall"

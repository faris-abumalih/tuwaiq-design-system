---
description: تركيب نظام تويق التصميمي في مشروع (جديد أو قائم) — توكنز، مكوّنات، فحص، CI
---

ركّب نظام تويق التصميمي في المشروع الحالي.

**اقرأ أولًا:** مهارة `tuwaiq-ds` → `references/new-project.md`

نفّذ بالترتيب، وتوقّف واسأل إذا وجدت تعارضًا مع إعداد قائم:

1. **افحص الوضع الحالي** — هل فيه `src/styles/theme.css`؟ مكتبة UI خارجية؟ إعداد i18n؟ Tailwind؟
   لخّص ما وجدته قبل ما تغيّر أي شيء.

2. **التوكنز**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gen_theme.py" src/styles/theme.css
   ```
   واربطه في `src/styles/index.css`.

3. **المكوّنات** — انسخ `${CLAUDE_PLUGIN_ROOT}/skills/tuwaiq-ds/assets/primitives/*` إلى
   `src/app/components/primitives/`، وانسخ `motion.css` واستورده.

4. **إعدادات الفحص** — انسخ `assets/ds.config.json` إلى جذر المشروع.

5. **CLAUDE.md** — ألحق محتوى `assets/CLAUDE.md.snippet` بملف `CLAUDE.md` (أنشئه إن لم يوجد).

6. **CI** — انسخ `assets/ds-lint.yml` إلى `.github/workflows/` وعدّل `OWNER` لرابط الريبو الصحيح.

7. **خط الأساس**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ds_lint.py" src
   ```
   اعرض العدد النهائي للأخطاء والتنبيهات، ثم:
   - مشروع جديد → لازم يكون صفرًا.
   - مشروع قائم → اعرض خطة ترحيل مرتّبة حسب أعلى أثر، ولا تبدأ التنفيذ قبل موافقة المستخدم.

$ARGUMENTS

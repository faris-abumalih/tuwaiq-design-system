# نظام تويق التصميمي — بلقن Claude Code

نظام تصميمي واحد لكل منتجات الفريق: **توكنز + مكوّنات + قواعد عربية RTL**،
مع **فحص إلزامي** يمنع أي كود مخالف قبل ما يُكتب.

## ليش بلقن ومو ملف توثيق؟

التوثيق يُقرأ مرة ويُنسى. البلقن:
- يحقن قواعد النظام في **كل جلسة** تلقائيًا (SessionStart)
- **يرفض** كتابة أي ملف يخالف النظام (PreToolUse)
- يعطي مسار عمل موحّد لبناء الصفحات (`/ds-page`)
- ونفس الفحص يشتغل في **CI** — فيلزم البشر مثل ما يلزم Claude

## التركيب

```bash
claude plugin marketplace add OWNER/tuwaiq-design-system
claude plugin install tuwaiq-ds@tuwaiq-design
```

للتجربة محليًا قبل الرفع:
```bash
claude plugin marketplace add /Users/user/Downloads/tuwaiq-design-system
claude plugin install tuwaiq-ds@tuwaiq-design
```

ثم في أي مشروع: `/ds-init`

## الاستخدام اليومي

| الأمر | متى |
|-------|-----|
| `/ds-init` | تركيب النظام في مشروع |
| `/ds-page <الميزة>` | بناء صفحة/ميزة جديدة بالمسار الكامل |
| `/ds-audit [diff]` | فحص المشروع أو التغييرات وإصلاحها |
| `/ds-token <سؤال>` | إيجاد التوكن الصحيح أو إضافة واحد جديد |
| وكيل `ds-reviewer` | مراجعة PR فيه واجهة |

فحص يدوي في أي وقت:
```bash
python3 plugins/tuwaiq-ds/scripts/ds_lint.py src
```

## البنية

```
.claude-plugin/marketplace.json      كتالوج البلقنات
plugins/tuwaiq-ds/
├── tokens/tokens.json               ← المصدر الوحيد للحقيقة
├── scripts/
│   ├── ds_lint.py                   محرّك الفحص (هوك + CI) — Python stdlib فقط
│   └── gen_theme.py                 يولّد theme.css من التوكنز
├── hooks/hooks.json                 PreToolUse (حجب) · PostToolUse (تنبيه) · SessionStart
├── commands/                        /ds-init /ds-page /ds-audit /ds-token
├── agents/ds-reviewer.md            مراجع الـ PR
└── skills/tuwaiq-ds/
    ├── SKILL.md                     القواعد الصلبة + مسار العمل
    ├── references/                  التوكنز · المكوّنات · الأنماط · RTL · الحالات · المبادئ · القائمة
    └── assets/
        ├── theme.css                مولَّد — لا يُعدّل
        ├── primitives/*.tsx         مكوّنات النظام جاهزة للنسخ
        ├── ds.config.json           إعدادات الفحص للمشروع
        └── ds-lint.yml              GitHub Action
```

## القواعد المفروضة آليًا

| القاعدة | المستوى |
|---------|---------|
| لا لون خام (`#hex`, `rgba()`, `bg-[#…]`) | حجب |
| لا مقاس خط خارج السلّم (12/13/14/15/16/20/28) | حجب |
| لا زاوية خارج السلّم (8/12/16/20/24/full) | حجب |
| لا خصائص اتجاهية فيزيائية (`marginLeft`, `ml-*`, `text-left`) | حجب |
| لا `<button>`/`<input>`/`<table>` خام خارج `primitives/` | حجب |
| لا نص عربي داخل الكود (i18n إلزامي) | حجب |
| لا خط مكتوب يدويًا | حجب |
| مسافة خارج السلّم · ظل خارج التوكنز · `dir="rtl"` ثابت | تنبيه |

**استثناء** (نادر، والسبب إجباري):
```tsx
background: X_BRAND, // ds-allow: no-raw-color — لون منصة X الرسمي
```

**تعطيل مؤقت** (للترحيل فقط): `DS_LINT_OFF=1`

## تعديل النظام

كل تغيير يمر على `tokens.json` ثم PR على هذا الريبو. **لا توكن محلي في مشروع.**
بعد الدمج، الفريق يحدّث:
```bash
claude plugin marketplace update tuwaiq-design
```

## المتطلبات

`python3` فقط (موجود افتراضيًا على macOS ولينكس). لا تنصيب، لا اعتماديات.

# مشروع جديد من الصفر

الهدف: أي واحد في الفريق يبدأ موقعًا جديدًا ويطلع بنفس الشكل من أول يوم.

## 1. الأساس التقني (لا نقاش)

```
React 19 + TypeScript + Vite
Tailwind v4 (عبر @tailwindcss/vite)
react-i18next   ← كل النصوص
lucide-react    ← الأيقونات، لا غيرها
react-router-dom
```
**ممنوع:** أي مكتبة UI جاهزة (MUI, AntD, Chakra, DaisyUI, shadcn كامل) — تكسر النظام.

## 2. البنية

```
src/
├── styles/
│   ├── theme.css        ← مولّد من tokens.json — لا يُعدّل يدويًا
│   └── index.css        ← @import theme + tailwind
├── app/
│   ├── components/
│   │   ├── primitives/  ← مكوّنات النظام (منسوخة من assets/primitives)
│   │   └── <feature>/   ← مكوّنات الميزة
│   ├── locales/ar/translation.json
│   └── pages/
└── main.tsx
ds.config.json           ← إعدادات الفحص
```

## 3. التركيب

```bash
# 1) التوكنز
python3 "$CLAUDE_PLUGIN_ROOT/scripts/gen_theme.py" src/styles/theme.css

# 2) المكوّنات الأساسية
cp "$CLAUDE_PLUGIN_ROOT/skills/tuwaiq-ds/assets/primitives/"*.tsx src/app/components/primitives/

# 3) إعدادات الفحص
cp "$CLAUDE_PLUGIN_ROOT/skills/tuwaiq-ds/assets/ds.config.json" .

# 4) الفحص في CI
mkdir -p .github/workflows
cp "$CLAUDE_PLUGIN_ROOT/skills/tuwaiq-ds/assets/ds-lint.yml" .github/workflows/
```

`index.css`:
```css
@import 'tailwindcss' source(none);
@source '../**/*.{ts,tsx}';
@import './theme.css';
```

`index.html`: `<html lang="ar" dir="rtl">`

## 4. أول شاشة

ابنِ بهذا الترتيب — لا تقفز:
1. **الحالة الفارغة** (شكل الشاشة قبل وجود بيانات)
2. **حالة التحميل** (هيكل عظمي)
3. المحتوى بصف واحد
4. المحتوى بكثرة (ترقيم، فلاتر)
5. حالات الخطأ وعدم الصلاحية

## 5. تأكيد الالتزام

```bash
python3 "$CLAUDE_PLUGIN_ROOT/scripts/ds_lint.py" src
```
صفر أخطاء قبل أول PR. المشروع الجديد يبدأ نظيفًا ويبقى نظيفًا — لا دَين تصميمي من اليوم الأول.

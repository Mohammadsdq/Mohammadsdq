# راه‌اندازی نسخه حرفه‌ای پروفایل Mohammadsdq

این نسخه با Python و GitHub GraphQL API داده‌های واقعی را دریافت می‌کند،
پنج کارت SVG تولید می‌کند و GitHub Actions هر روز آن‌ها را به‌روزرسانی می‌کند.

## خروجی‌ها
- `cards/hero.svg`: نام، Bio و معرفی
- `cards/stats.svg`: مخازن عمومی، Followers، مجموع ستاره‌ها و Contribution یک سال اخیر
- `cards/activity.svg`: تقویم واقعی Contribution در ۳۶۵ روز گذشته
- `cards/languages.svg`: زبان اصلی مخازن عمومی
- `cards/repositories.svg`: شش مخزن عمومی برتر بر اساس ستاره
- `data/github_stats.json`: داده خام دریافت‌شده از GitHub

## ۱. Profile Repository
در GitHub باید یک repository عمومی با نام دقیق `Mohammadsdq` داشته باشی.
اگر از قبل ساخته‌ای، فایل‌های این پروژه را در همان repository قرار بده.

## ۲. ساخت Token
1. GitHub → Settings → Developer settings → Personal access tokens
2. یک Fine-grained token بساز.
3. دسترسی را حداقلی نگه دار؛ اطلاعات عمومی برای این نسخه کافی است.
4. برای شمردن Contribution مخازن خصوصی، scope دسترسی `read:user` لازم است.
5. توکن را کپی کن.

**توکن را هرگز داخل کد، README یا فایل JSON قرار نده.**

## ۳. افزودن Secret
در repository برو به:
`Settings → Secrets and variables → Actions → New repository secret`

نام را دقیقاً `GH_TOKEN` بگذار و مقدار را Token کپی‌شده قرار بده.

## ۴. اجرای خودکار
1. فایل‌ها را روی branch اصلی `main` push کن.
2. در تب Actions اجرای Workflowها را فعال کن.
3. Workflow با نام `Update GitHub profile cards` را باز کن.
4. `Run workflow` را بزن.
5. پس از اجرای موفق، کارت‌ها و `github_stats.json` به‌روز و commit می‌شوند.
6. پس از آن هر روز ساعت 00:23 UTC اجرا می‌شود؛ GitHub ممکن است در زمان شلوغی اجرا را کمی عقب بیندازد.

## ۵. اجرای محلی (اختیاری)

Windows PowerShell:
```powershell
$env:GH_TOKEN="YOUR_TOKEN"
$env:GITHUB_USERNAME="Mohammadsdq"
python scripts/generate_profile.py
```

Linux/macOS:
```bash
export GH_TOKEN="YOUR_TOKEN"
export GITHUB_USERNAME="Mohammadsdq"
python scripts/generate_profile.py
```

Python 3.10+ کافی است و هیچ dependency خارجی لازم نیست.

## نکات دقت
- Contribution از `contributionsCollection.contributionCalendar` خوانده می‌شود.
- تعداد مخازن، Followers و Following از GraphQL می‌آید.
- ستاره‌ها و Forkها از مخازن عمومی غیر Fork که مالکشان حساب کاربر است محاسبه می‌شوند.
- اسکن مخازن برای ستاره و زبان تا سقف ۱۰۰۰ مخزن است؛ بالاتر از آن این آمار ممکن است ناقص شود.
- نمودار زبان بر اساس زبان اصلی هر repository است، نه ساعت واقعی برنامه‌نویسی.
- انیمیشن‌ها با `prefers-reduced-motion` غیرفعال می‌شوند.
- Workflow فقط کارت‌ها و JSON را commit می‌کند.

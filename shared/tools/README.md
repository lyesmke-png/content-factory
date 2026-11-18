# tools — الأدوات المتاحة والسكربتات المساعدة

## 1. الـ connectors المتاحة في الجلسة

| الأداة | ما تقدّمه فعليًا | من يستخدمها |
|---|---|---|
| **Heg — الصور** | `generate_image` / `generate_image_batch`، `upscale_image`، `remove_background`، `outpaint_image`، `reframe` (لتحويل إلى 9:16)، `estimate_image_cost` | `visual-production` |
| **Heg — الفيديو** | `generate_video` / `generate_video_batch`، `upscale_video`، `estimate_video_cost`، `motion_control` / `animation_actions` | `visual-production` |
| **Heg — الصوت** | `generate_audio` / `generate_audio_batch`، `list_voices`، `create_voice`، `voice_change`، `separate_stems`، `estimate_audio_cost` | `visual-production` |
| **Heg — التحليل** | `video_analysis_create` / `video_analysis_status` (تحليل فيديو مرجعي)، `virality_predictor` (تقييم فكرة قبل الإنتاج)، `tiktok_music_trending` (الموسيقى الرائجة) | `trend-research` |
| **Heg — النشر** | `tiktok_accounts`، `tiktok_connect`، `tiktok_prepare_publish`، `tiktok_publish_status` | `publish-and-log` (بعد الموافقة فقط) |
| **Heg — الإدارة** | `balance`، `transactions`، `jobs_wait`، `show_generation_by_ids`، `list_projects` | كل سكيل يولّد |
| **Figma** | `create_new_file`، `create_session`، `use_figma`، `generate_image`، `get_screenshot`، `download_assets` — للصور المصغّرة والقوالب النصية والهوية | `visual-production` |
| **بحث الويب** | `WebSearch` + قراءة الصفحات — لرصد المنتشر والترندات والهاشتاقات وسياسات المنصات | `trend-research` |
| **GitHub (`gh`)** | إدارة المستودع والـ issues | كل السكيلات (commit/push) |
| **Claude Docs** | مستندات قابلة للمشاركة والتعليق — لعرض التقارير على المالك عند الطلب | اختياري |

### حدود يجب معرفتها
- **لا نشر آلي إلى YouTube Shorts** في الأدوات الحالية. TikTok فقط عبر Heg.
  YouTube ⇒ حزمة رفع يدوي يجهّزها `publish-and-log`.
- **لا قياس تحليلي آلي** من TikTok أو YouTube: أرقام `analytics.md` تأتي من المالك.
- **لا واجهة رسمية لاستعراض «الأكثر انتشارًا»** في TikTok/YouTube: تحليل المنتشر
  يعتمد على البحث على الويب، لذا تُعلَّم الأرقام «تقديري» مع المصدر.
- كل توليد في Heg **مدفوع**: التقدير والموافقة قبل التنفيذ (انظر `visual-production`).

## 2. السكربتات المساعدة

| السكربت | الاستخدام |
|---|---|
| `new-script.py` | ينشئ ملف سكريبت جديد من القالب بالتاريخ والـ slug. |
| `backlog-summary.py` | يلخّص بنك أفكار نيش مرتّبًا حسب الأولوية. |

```bash
python shared/tools/new-script.py ai-short-films "الباب الأخير"
python shared/tools/backlog-summary.py kids-films --top 5
```

كلاهما بلا تبعيات (Python 3 القياسي) ويعمل على Windows وLinux.

## 3. أدوات مقترحة غير مثبّتة (قرار المالك)

| الأداة | لماذا | الملاحظة |
|---|---|---|
| **YouTube Data API v3** | رفع الفيديو آليًا مع ضبط `madeForKids`، وسحب أرقام المشاهدات والإكمال إلى `analytics.md` | مجاني بحصة يومية؛ يحتاج مشروع Google Cloud وOAuth. يُخزَّن السر خارج المستودع. |
| **TikTok Display API** | سحب أرقام منشوراتنا آليًا بدل الإدخال اليدوي | يحتاج تسجيل تطبيق ومراجعة من TikTok. |
| **أرشيف ترند (مثل أدوات رصد الهاشتاقات)** | بيانات انتشار أدق من البحث على الويب | معظمها مدفوع بالاشتراك — يُقيَّم بعد ثبوت الإقبال. |
| **مكتبة موسيقى مرخّصة** | صوت ثابت للعلامة دون مخاطرة حقوق | مدفوع؛ يُؤجَّل حتى تثبيت الهوية الصوتية. |

لم يُثبَّت أي منها. التثبيت ينتظر قرار المالك.

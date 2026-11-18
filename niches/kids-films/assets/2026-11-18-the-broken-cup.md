# أصول — سمسم كسر الكوب — 2026-11-18

- السكريبت: `niches/kids-films/scripts/2026-11-18-the-broken-cup.md`
- أداة التوليد: Heg — `gpt_image_2_6` (صور ثابتة 9:16)
- **الحالة: لم تُولَّد — محجوبة على مستوى خطة الحساب**

> لا ملفات ثقيلة في المستودع. الروابط والوصف فقط.

## ⚠ سبب التوقف (2026-11-18)
وافق المالك على ميزانية ≈2.25 كريدت لتوليد 9 صور لهذا الفيديو. عند التنفيذ ردّ
Heg على كل الطلبات التسعة بـ:

```
submission_failed — Requires basic plan or higher.
```

وتكرّر الرفض نفسه مع موديل بديل (`recraft_v4_1`) ⇒ **الحجب على مستوى خطة الحساب
لا على مستوى الرصيد**. الرصيد 10 كريدت موجود لكنه غير قابل للإنفاق على خطة `free`.
**لم يُخصم أي كريدت** (0/9 طلبات مُرسَلة).

ما يلزم للمتابعة: ترقية خطة Heg إلى `basic` أو أعلى. بعدها تُنفَّذ الـ prompts أدناه
كما هي بلا تعديل، فهي مُعدّة ومُراجَعة.

## التقديرات الفعلية (مقيسة في 2026-11-18)
| العنصر | التقدير |
|---|---|
| صورة واحدة 9:16 (`gpt_image_2_6`) | 0.25 كريدت |
| 9 صور (لوحة هذا الفيديو) | 2.25 كريدت |
| مقطع فيديو 5 ث صامت (`kling3_0` std) | 7.5 كريدت |
| فيديو كامل (7 مقاطع × 5 ث) | ≈ 52.5 كريدت |
| مقطع 5 ث بجودة 1080p (`seedance_2_5`) | 80 كريدت |

## جدول الأصول (يُملأ عند التوليد)
| # | النوع | الوصف | الأداة / الموديل | المعرّف (job id) | الرابط | اللقطة في السكريبت |
|---|---|---|---|---|---|---|
| 1 | صورة | المطبخ فارغًا — لقطة تأسيسية | gpt_image_2_6 | — | — | اللقطة 1 |
| 2 | صورة | سمسم على الطاولة والكوب يسقط | gpt_image_2_6 | — | — | اللقطة 2 (Hook) |
| 3 | صورة | سمسم ينظر إلى القطعتين | gpt_image_2_6 | — | — | اللقطة 3 |
| 4 | صورة | سمسم يخفي القطعتين ويجلس فوق السجادة | gpt_image_2_6 | — | — | اللقطة 4 |
| 5 | صورة | نور تبحث وترفع وسادة | gpt_image_2_6 | — | — | اللقطة 5 |
| 6 | صورة | لقطة قريبة على وجه سمسم مترددًا | gpt_image_2_6 | — | — | اللقطة 6 |
| 7 | صورة | سمسم يسحب السجادة بفمه | gpt_image_2_6 | — | — | اللقطة 7 |
| 8 | صورة | نور تربّت على رأس سمسم | gpt_image_2_6 | — | — | اللقطة 8 |
| 9 | صورة | الاثنان يحملان القطعتين إلى الطاولة | gpt_image_2_6 | — | — | اللقطة 9 |

## كتلة الشخصيات الثابتة (تُنسخ حرفيًا في كل prompt، وفي كل فيديو قادم)

**نور:**
```
Noor, a 6-year-old girl, warm light-brown skin, big dark-brown eyes, round friendly
face, hair in two braids tied with small red bands, bright yellow buttoned coat over
a white shirt, dark blue trousers, white sneakers.
```

**سمسم:**
```
Samsam, a small grey kitten with soft fur, LEFT ear folded down, big round amber eyes,
tiny pink nose, no collar.
```

**كتلة الأسلوب:**
```
Soft 3D animated children's film style, Pixar-like rounded shapes, bright daytime
lighting, warm pastel-saturated palette, no harsh shadows, friendly and safe,
vertical 9:16 composition, no text and no lettering anywhere.
```

> هذه الكتل الثلاث هي عقد الثبات البصري للنيش. أي تغيير فيها يكسر تعرّف الطفل على
> الشخصية ⇒ لا تُعدَّل إلا بقرار مالك صريح، ومعها يُثبَّت الـ seed عند أول توليد ناجح.

## الـ prompts الكاملة (جاهزة للتنفيذ)

**1 — المطبخ فارغًا**
```
<كتلة الأسلوب> SCENE: an empty cheerful kitchen interior in the morning, large window
with soft sunlight, light wooden table, pale mint cabinets, a small colourful round rug
on the floor. Wide establishing shot, nothing scary, cosy and inviting.
```

**2 — الـ Hook: الكوب يسقط**
```
<كتلة الأسلوب> CHARACTER (keep exactly): <سمسم> SCENE: Samsam standing on a light
wooden kitchen table, frozen mid-motion with wide surprised eyes, while a blue ceramic
cup tips over the edge of the table and begins to fall out of frame. Bright cheerful
kitchen behind, large sunny window. Comedic surprise, nothing frightening.
```

**3 — القطعتان على الأرض**
```
<كتلة الأسلوب> CHARACTER (keep exactly): <سمسم> SCENE: Samsam sitting on the kitchen
floor looking down guiltily at TWO large smooth rounded pieces of a broken blue cup,
the pieces clearly blunt and harmless with no sharp shards, tail curled with worry.
Bright safe kitchen, sunny.
```

**4 — الإخفاء**
```
<كتلة الأسلوب> CHARACTER (keep exactly): <سمسم> SCENE: Samsam pushing the two blunt
rounded cup pieces under a small colourful round rug with one paw, then sitting on top
of the rug with an exaggerated innocent forced smile, eyes glancing sideways. Comedy,
bright sunny kitchen.
```

**5 — نور تبحث**
```
<كتلة الأسلوب> CHARACTER (keep exactly): <نور> SCENE: Noor searching the cheerful
kitchen, lifting a cushion off a chair and peering under it with a puzzled curious
expression. Sunny bright room, cosy and safe.
```

**6 — التردد**
```
<كتلة الأسلوب> CHARACTER (keep exactly): <سمسم> SCENE: tight close-up on Samsam's
face, hesitating, the folded left ear drooping lower, eyes looking up and to the side
with a gentle guilty expression, mouth slightly closed. Soft blurred bright kitchen
background. Tender, not sad, not scary.
```

**7 — الاعتراف**
```
<كتلة الأسلوب> CHARACTER (keep exactly): <سمسم> SCENE: Samsam pulling the corner of a
small colourful round rug with his mouth, dragging it aside so that two large blunt
rounded blue cup pieces are revealed underneath. Brave honest little gesture, bright
sunny kitchen floor.
```

**8 — العفو**
```
<كتلة الأسلوب> CHARACTERS (keep exactly): <نور> <سمسم> SCENE: Noor sitting cross-legged
on the kitchen floor beside Samsam, smiling warmly and gently patting his head; Samsam
rests his head on her hand, relieved. Warm forgiving moment, sunlight from the window.
```

**9 — النهاية**
```
<كتلة الأسلوب> CHARACTERS (keep exactly): <نور> <سمسم> SCENE: wide shot, Noor and
Samsam carrying the two blunt rounded blue cup pieces together towards the light wooden
table, working as a team, both content; bright sunny kitchen window behind them.
Happy ending, safe and cheerful.
```

## ملاحظات
- التكلفة الفعلية: **0 كريدت** (لم يُرسَل أي طلب).
- كل prompt يذكر صراحةً أن قطع الكوب **كبيرة وناعمة الحواف بلا شظايا** — بند
  «لا سلوك خطِر قابل للتقليد» في فحص امتثال الأطفال.
- كل prompt يمنع أي نص أو حروف في الصورة: النص العربي يُضاف في التحرير لا في التوليد
  (موديلات الصور لا تُنتج عربية صحيحة).

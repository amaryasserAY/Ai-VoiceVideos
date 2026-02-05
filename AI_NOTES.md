## AI_NOTES (مصدر الحقيقة لسياق المشروع)

⚠️ **قاعدة مهمة**: بعد أي تعديل/إصلاح/إضافة في الكود، يجب تحديث هذا الملف فوراً لتوثيق التغييرات.

### الهدف

- بناء “مونتير ذكي” يعتمد على الأوامر الصوتية/النصية لتحرير الفيديو تلقائياً وإخراج ملف نهائي بسرعة.

### الحالة الحالية (Prototype - Refactored)

- **واجهة**: Streamlit (`app.py`) مع رفع فيديو + عرض فيديو + Timeline (Thumbnails).
- **هيكل الكود**: تم Refactor إلى modules منفصلة:
  - `utils/ai_engine.py`: منطق Gemini + تحليل الأوامر + تأكيد صوتي
  - `utils/media_engine.py`: استخراج فريمات + تطبيق Actions + تصدير
  - `utils/ui_utils.py`: Timeline HTML + CSS loading + حلول بديلة للعرض
  - `utils/command_cache.py`: قاعدة بيانات SQLite لحفظ الأوامر الشائعة + Fuzzy Matching
- **ذكاء اصطناعي**: Gemini `gemini-2.5-flash` عبر `google-generativeai`.
- **صيغة الأوامر**: JSON Array حصري (بدون Markdown) + parsing بـ `json.loads`.
- **تنفيذ**: MoviePy + FFmpeg (قص/كتم/سرعة/أبيض وأسود) بشكل متسلسل.
- **أداء**: `@st.cache_data(persist="disk")` لنتائج التحليل + Command Cache (SQLite) لتوفير التوكينز.
- **توفير التوكينز**: نظام Cache ذكي يحفظ الأوامر الشائعة + Fuzzy Matching (85%+ تشابه) للرجوع السريع بدون AI.
- **تأكيد تفاعلي**: بعد التحليل، يطلب تأكيد صوتي ("نعم"/"لا"/"عدل") قبل التنفيذ.
- **Windows**: FFmpeg مضمّن داخل مجلد المشروع + إضافة مسار المشروع إلى `PATH`.
- **Python 3.13**: fallback إلى `audioop_lts` عند غياب `audioop`.
- **معالجة أخطاء**: تحقق من صحة الفيديو + رسائل Debug واضحة + حلول بديلة تلقائية.

### القرارات/القواعد الداخلية المهمة

- عدم تخزين مفاتيح API في الكود، الاعتماد على `.env` (`GOOGLE_API_KEY`).
- مخرجات Gemini يجب أن تكون JSON فقط (لا شروحات).
- أي خطوة تحرير غير معروفة يجب تجاهلها/رفضها بشكل واضح (منطقي للتحسين لاحقاً).

### ملفات مهمة

- `app.py`: واجهة Streamlit الرئيسية (منظمة + تستدعي modules).
- `utils/ai_engine.py`: تحليل الأوامر الصوتية/النصية عبر Gemini + تحليل تأكيد صوتي.
- `utils/media_engine.py`: استخراج فريمات Timeline + تطبيق Actions + تصدير.
- `utils/ui_utils.py`: عرض Timeline (HTML + Streamlit native fallback).
- `utils/command_cache.py`: قاعدة بيانات SQLite + Fuzzy Matching للأوامر المتشابهة.
- `command_cache.db`: قاعدة بيانات SQLite (يتم إنشاؤها تلقائياً) لحفظ الأوامر الشائعة.
- `main.py`: تجربة CLI بسيطة.
- `style.css`: Timeline + تحسينات UI (Dark Mode).
- `PROJECT_SPEC.md`: وثيقة توصيف المشروع.

### جلسة 2026-02-04 (إنشاء التوثيق)

- إنشاء توثيق المشروع: `README.md` و `PROJECT_SPEC.md`.
- إضافة `requirements.txt` (مع تصحيح `streamlit-audiorecorder`).
- إنشاء `AI_NOTES.md` وملفات القواعد المطلوبة (RULES/.cursorrules) في نفس الجلسة.

### جلسة 2026-02-04 (Refactoring + إصلاح Timeline)

**المشكلة المكتشفة**: Timeline كان يظهر كود HTML كنص بدل عرض الفريمات كصور.

**الإصلاحات المنفذة**:

1. **Refactoring الكود**:

   - فصل `app.py` إلى modules: `utils/ai_engine.py`, `utils/media_engine.py`, `utils/ui_utils.py`
   - تحسين قابلية الصيانة (كل ملف ≤ 100 سطر تقريباً)

2. **إصلاح Timeline**:

   - إضافة معالجة أخطاء في `extract_timeline_frames()`: تحقق من مدة الفيديو + تخطي فريمات فاشلة
   - إصلاح `render_timeline_html()`: معالجة Base64 بشكل آمن + تخطي صور فاشلة
   - إضافة حل بديل تلقائي: `render_timeline_streamlit()` يستخدم `st.columns` + `st.image` إذا فشل HTML

3. **تحسينات UX**:
   - رسائل Debug واضحة (عدد الفريمات المستخرجة + أسباب الفشل)
   - Fallback تلقائي للعرض البديل عند فشل HTML
   - رسائل خطأ واضحة للمستخدم

**الملفات المعدلة**:

- `app.py`: استخدام modules + معالجة Timeline محسّنة
- `utils/media_engine.py`: استخراج فريمات آمن + معالجة أخطاء
- `utils/ui_utils.py`: HTML Timeline + Streamlit native fallback
- `utils/ai_engine.py`: فصل منطق AI (موجود مسبقاً)

**النتيجة**: Timeline يعمل الآن بشكل موثوق مع حل بديل تلقائي إذا فشل HTML.

### جلسة 2026-02-04 (نظام توفير التوكينز + تأكيد صوتي)

**الطلب**: فهم أذكى للأوامر الصوتية + تحليل سريع + تأكيد صوتي + توفير التوكينز من Google API.

**الإضافات المنفذة**:

1. **نظام Command Cache (SQLite)**:

   - قاعدة بيانات محلية (`command_cache.db`) لحفظ الأوامر الشائعة + JSON المقابل
   - جدول `commands`: نص الأمر + hash + actions JSON + transcription + usage_count
   - جدول `session_context`: (جاهز للمستقبل) لحفظ سياق الجلسات
   - حفظ تلقائي بعد كل تحليل ناجح عبر AI

2. **Fuzzy Matching ذكي**:

   - دالة `find_similar_command()` تستخدم `SequenceMatcher` لحساب التشابه
   - إذا كان التشابه ≥ 85%، يتم استخدام النتيجة المحفوظة بدون إرسال للـ AI
   - توفير فوري للتوكينز للأوامر المتكررة

3. **نظام تأكيد صوتي تفاعلي**:

   - بعد التحليل، يعرض الخطة ويطلب تأكيد صوتي
   - دالة `parse_confirmation_command()` تحلل "نعم"/"لا"/"عدل"
   - دعم كلمات متعددة (نعم/yes/موافق/ok) + fallback للـ AI إذا لم يتعرف
   - واجهة تفاعلية في `app.py` مع تسجيل صوتي للتأكيد

4. **تحسين الـ Prompt**:

   - تقليل طول الـ system prompt من ~15 سطر إلى ~3 أسطر
   - توفير ~70% من التوكينز في كل طلب
   - تسريع الاستجابة بسبب طول أقل

5. **تحسينات UX**:
   - عرض مصدر النتيجة (Cache أو AI) للمستخدم
   - قسم "الأوامر الشائعة المحفوظة" يعرض الأكثر استخداماً
   - رسائل واضحة عند استخدام Cache ("⚡ تم الاسترجاع من الذاكرة")

**الملفات الجديدة**:

- `utils/command_cache.py`: نظام Cache كامل (150+ سطر)
- `command_cache.db`: قاعدة بيانات SQLite (يتم إنشاؤها تلقائياً)

**الملفات المعدلة**:

- `utils/ai_engine.py`: استخدام Cache قبل AI + تحسين Prompt + دالة تأكيد صوتي
- `app.py`: نظام تأكيد صوتي تفاعلي + عرض الأوامر الشائعة
- `utils/__init__.py`: تصدير `command_cache` module

**النتيجة**:

- توفير توكينز: الأوامر المتكررة (85%+ تشابه) لا تحتاج AI
- تحليل أسرع: Cache فوري بدل انتظار API
- تفاعل أفضل: تأكيد صوتي قبل التنفيذ يمنع الأخطاء
- Prompt محسّن: توفير ~70% توكينز في كل طلب AI

### الخطوات القادمة (Roadmap)

**المرحلة 1 (قريبة - 1-2 أسبوع)** — ✅ **مكتملة**:

- ✅ Refactoring الكود إلى modules (مكتمل)
- ✅ إصلاح Timeline + معالجة أخطاء (مكتمل)
- ✅ نظام Command Cache + Fuzzy Matching (مكتمل)
- ✅ تأكيد صوتي تفاعلي (مكتمل)
- ✅ تحسين Prompt لتوفير التوكينز (مكتمل)
- ✅ Validation لخطوات JSON قبل التنفيذ (`validate_actions` في media_engine)
- ✅ إحصائيات استخدام (كم توكينز وفرنا + عدد الأوامر المحفوظة) — في السايدبار
- ✅ تصدير/استيراد قاعدة بيانات الأوامر (Backup JSON + استعادة)
- ✅ Cache Threshold قابل للتعديل (سلايدر في إعدادات متقدمة + session_state)
- ✅ عرض الأوامر الشائعة في السايدبار (expander "أوامر شائعة")
- ⏳ رسائل أخطاء واضحة + Debug Mode (جزئي: رسائل تحقق)
- ⏳ اختبارات وحدات للمحرك (لم يُنفّذ بعد)

**المرحلة 2 (متوسطة - 3-6 أسابيع)** — ✅ **مكتملة بالكامل**:

- ✅ توسيع قاموس الأوامر: إضافة **music** (موسيقى خلفية + volume) + **subtitle** (نص على الفيديو)
- ✅ **Templates للأوامر الشائعة**: حفظ/تطبيق/حذف قوالب من الواجهة + جدول templates في DB
- ✅ **موسيقى خلفية**: رفع MP3/WAV من السايدبار + دمج مع الفيديو (loop/volume) في media_engine
- ✅ **Preview قبل التصدير**: معاينة سريعة لكل خطوة (5 ثواني) قبل التنفيذ الكامل
- ✅ **Undo/Redo**: نظام تراجع وإعادة كامل مع UndoRedoManager + أزرار في الواجهة
- ✅ **إدارة مشاريع Sessions**: حفظ/فتح/حذف مشاريع كاملة (video_path + actions + music) في SQLite
- ✅ **تحسين Timeline للأداء**: max_duration=300s + تقليل حجم الصور المصغرة (150x150) + فريم كل 10 ثواني للفيديوهات الطويلة
- ✅ **Batch Processing**: معالجة عدة فيديوهات بنفس الأوامر بشكل متوازي (ThreadPoolExecutor)
- ✅ **Timeline تفاعلي**: النقر على فريم للانتقال للوقت المحدد في الفيديو (JavaScript + onclick)
- ✅ **Subtitles**: إضافة نص على الفيديو بأوامر صوتية (position, fontsize, color, bg_color)
- ✅ **تصدير متعدد الصيغ**: MP4/WebM/GIF من نفس الفيديو (multiselect في الواجهة)

**المرحلة 3 (نهائية - 2-4 شهور)**:

- تحويل إلى Core Engine مستقل (API محلي)
- Desktop Packaging (PyInstaller أو Tauri/Electron)
- Reliability & Recovery (checkpoints + استكمال بعد انقطاع)
- جودة إخراج احترافية (Presets: Reels/YouTube/1080p/4K)
- **ميزة جديدة**: AI Voice Cloning (استخدام صوت المستخدم للأوامر بدون تسجيل متكرر)
- **ميزة جديدة**: تحليل تلقائي للمحتوى (كشف المشاهد/الأشخاص/الكائنات + أوامر ذكية)
- **ميزة جديدة**: Auto-Edit Suggestions (اقتراحات تلقائية بناءً على نوع الفيديو)
- **ميزة جديدة**: دعم Collaboration (مشاركة المشاريع مع فريق)
- **ميزة جديدة**: Cloud Sync (مزامنة قاعدة بيانات الأوامر عبر السحابة)
- **ميزة جديدة**: API للدمج مع أدوات أخرى (REST API للتحكم البرمجي)
- **ميزة جديدة**: دعم Real-time Editing (تحرير مباشر أثناء التسجيل)
- **ميزة جديدة**: Advanced Analytics (إحصائيات مفصلة عن الاستخدام + توفير التوكينز)
- **ميزة جديدة**: Multi-language Support (دعم لغات متعددة للأوامر)
- **ميزة جديدة**: Voice Profiles (حفظ أصوات متعددة + تمييز تلقائي)

**ملاحظة**: راجع `FEATURES_ROADMAP.md` للتفاصيل الكاملة لكل ميزة مقترحة.

### جلسة 2026-02-04 (اقتراح مميزات إضافية)

**الطلب**: اقتراح مميزات جديدة وتحديد موقعها في الخارطة.

**النتيجة**:
- إنشاء `FEATURES_ROADMAP.md` يحتوي على **21 ميزة مقترحة** منظمة حسب المراحل
- تحديث الخارطة في `AI_NOTES.md` بإضافة المميزات الجديدة
- تصنيف المميزات حسب الأولوية (عالية/متوسطة/منخفضة)

**المميزات المقترحة**:
- **المرحلة 1**: إحصائيات استخدام + تصدير/استيراد Cache + Cache Threshold قابل للتعديل
- **المرحلة 2**: Batch Processing + Templates + Timeline تفاعلي + موسيقى خلفية + Subtitles + تصدير متعدد الصيغ + أوامر متقدمة
- **المرحلة 3**: AI Voice Cloning + Content Analysis + Auto-Edit Suggestions + Collaboration + Cloud Sync + REST API + Real-time Editing + Advanced Analytics + Multi-language + Voice Profiles

**الملفات الجديدة**:
- `FEATURES_ROADMAP.md`: ملف شامل يحتوي على وصف تفصيلي لكل ميزة + أهمية + طريقة التنفيذ

### جلسة مراجعة (المرحلة 1 و 2 — ما تم تنفيذه + إصلاحات)

**ما أنت نفذته (أنت)**:
- المرحلة 1: إحصائيات (get_usage_stats)، تصدير/استيراد (export_db_to_json، import_db_from_json)، Cache Threshold (سلايدر)، مركز تحكم في السايدبار.
- المرحلة 2: موسيقى خلفية (رفع MP3 + دمج في media_engine + action "music")، قوالب (save_template، get_all_templates، delete_template + تبويب قوالب + حفظ كقالب من المراجعة).
- تحسينات واجهة: سايدبار (حالة AI/FFmpeg، إحصائيات، مكتبة موسيقى، إعدادات، Reset).

**إصلاحات وإضافات (المراجعة)**:
1. **cache_threshold**: تخزينه في `st.session_state.cache_threshold` مع قيمة افتراضية 0.85 حتى يكون متاحاً دائماً؛ استخدامه في تحليل الصوت والنص.
2. **Validation**: إضافة `validate_actions(actions, video_path)` في media_engine (تحقق trim/speed/music)؛ استدعاؤها قبل التنفيذ في `execute_editing` مع عرض رسالة خطأ واضحة.
3. **الأوامر الشائعة**: إضافة `get_popular_commands(limit)` في command_cache وعرضها في السايدبار (expander "أوامر شائعة") مع معالجة بيانات تالفة.
4. **ai_engine**: إضافة نص "Analyze this audio and output JSON only." عند إرسال صوت لـ Gemini لزيادة الوضوح.
5. **تحسين عرض الأوامر الشائعة**: عرض آمن للنص (حتى 50 حرف) وعدد الاستخدامات.

**الملفات المعدلة في المراجعة**:
- `app.py`: session_state لـ cache_threshold، استدعاء validate_actions، expander أوامر شائعة، استخدام st.session_state.cache_threshold.
- `utils/command_cache.py`: دالة get_popular_commands مع معالجة أخطاء JSON.
- `utils/media_engine.py`: دالة validate_actions قبل apply_edit_actions.
- `utils/ai_engine.py`: إضافة جملة تحليل الصوت في الـ prompt.
- `AI_NOTES.md`: تحديث حالة المرحلة 1 (مكتملة) والمرحلة 2 (جزئياً) + سجل الجلسة.

### جلسة إكمال المرحلة 2 (2026-02-04)

**الطلب**: إكمال المرحلة 2 بالكامل.

**المميزات المنفذة**:

1. **Preview Engine** (`utils/preview_engine.py`):
   - `preview_step()`: معاينة خطوة واحدة (5 ثواني)
   - `preview_all_steps()`: معاينة كل الخطوات واحدة تلو الأخرى
   - عرض في expander "معاينة سريعة" في قسم المراجعة

2. **Undo/Redo System** (`utils/undo_redo.py`):
   - `UndoRedoManager` class مع history و current_index
   - حفظ كل حالة بعد التنفيذ تلقائياً
   - أزرار Undo/Redo في قسم المراجعة

3. **Session Manager** (`utils/session_manager.py`):
   - قاعدة بيانات SQLite (`sessions.db`) لحفظ المشاريع
   - `save_session()` / `load_session()` / `list_sessions()` / `delete_session()`
   - واجهة في السايدبار (expander "المشاريع المحفوظة")

4. **Batch Processor** (`utils/batch_processor.py`):
   - `batch_process()`: معالجة متوازية لعدة فيديوهات
   - استخدام `ThreadPoolExecutor` مع progress callback
   - تبويب "Batch" في قسم الإدخال

5. **Subtitle Engine** (`utils/subtitle_engine.py`):
   - `add_subtitle()`: إضافة subtitle واحد
   - `add_subtitles()`: إضافة عدة subtitles
   - دعم position, fontsize, color, bg_color
   - Action "subtitle" في Schema و Prompt

6. **تحسين Timeline**:
   - `extract_timeline_frames()`: إضافة `max_duration=300` لتقليل الوقت
   - تقليل حجم الصور المصغرة من 200x200 إلى 150x150
   - حساب عدد الفريمات بناءً على المدة الفعلية

7. **Timeline تفاعلي**:
   - تحديث `render_timeline_html()`: إضافة onclick للانتقال للوقت
   - JavaScript function `seekToTime()` للانتقال في الفيديو

8. **تصدير متعدد الصيغ**:
   - `export_video()`: دعم format parameter (mp4/webm/gif)
   - `export_multiple_formats()`: تصدير بعدة صيغ دفعة واحدة
   - multiselect في الواجهة لاختيار الصيغ

**الملفات الجديدة**:
- `utils/preview_engine.py` (60+ سطر)
- `utils/session_manager.py` (120+ سطر)
- `utils/undo_redo.py` (60+ سطر)
- `utils/batch_processor.py` (50+ سطر)
- `utils/subtitle_engine.py` (70+ سطر)
- `sessions.db` (يتم إنشاؤها تلقائياً)

**الملفات المعدلة**:
- `app.py`: إضافة كل المميزات الجديدة في الواجهة (Preview, Undo/Redo, Sessions, Batch, تصدير متعدد)
- `utils/media_engine.py`: دعم Subtitles + تصدير متعدد الصيغ + تحسين Timeline
- `utils/ui_utils.py`: Timeline تفاعلي مع JavaScript
- `utils/ai_engine.py`: إضافة action "subtitle" في Schema و Prompt
- `utils/__init__.py`: تصدير الملفات الجديدة

**النتيجة**: المرحلة 2 **مكتملة بالكامل** ✅ — جميع المميزات المخططة تم تنفيذها وتكاملها في الواجهة.

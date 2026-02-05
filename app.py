import os
import sys
import streamlit as st
import tempfile
import time
import json
from dotenv import load_dotenv
from audiorecorder import audiorecorder

# --- System Fixes ---
os.environ["PATH"] += os.pathsep + os.getcwd()
try:
    import audioop
except ImportError:
    import audioop_lts
    sys.modules['audioop'] = audioop_lts

from utils import (ui_utils, ai_engine, media_engine, command_cache, 
                   preview_engine, session_manager, undo_redo, batch_processor, subtitle_engine)
from utils.config import validate_dependencies, get_ffmpeg_path
from moviepy.editor import VideoFileClip

# --- Initialization ---
load_dotenv()
st.set_page_config(
    page_title="🏛️ AI Video Editor Pro - Pharaoh Edition",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"  # خلي Sidebar مطوي افتراضياً
)
ui_utils.load_css("style.css")

# ✅ FFmpeg Validation
deps = validate_dependencies()
if not deps['ffmpeg']:
    st.error("""
    ## ⚠️ FFmpeg غير موجود!
    
    البرنامج يحتاج FFmpeg للعمل. حل المشكلة:
    
    1. حمّل FFmpeg من: https://ffmpeg.org/download.html
    2. فك الضغط وانسخ ffmpeg.exe في نفس مجلد البرنامج
    3. أعد تشغيل البرنامج
    
    💡 ملاحظة: الملف موجود بالفعل في المجلد (ffmpeg.exe)
    """)
    st.stop()

# --- Session State Initialization ---
if 'ai_result' not in st.session_state: 
    st.session_state.ai_result = None
if 'waiting_confirmation' not in st.session_state: 
    st.session_state.waiting_confirmation = False
if 'music_path' not in st.session_state: 
    st.session_state.music_path = None
if 'cache_threshold' not in st.session_state: 
    st.session_state.cache_threshold = 0.85
if 'undo_redo_manager' not in st.session_state:
    st.session_state.undo_redo_manager = undo_redo.UndoRedoManager()
if 'current_video_path' not in st.session_state: 
    st.session_state.current_video_path = None
if 'preview_mode' not in st.session_state: 
    st.session_state.preview_mode = False
if 'show_stats' not in st.session_state:
    st.session_state.show_stats = False
if 'selected_formats' not in st.session_state:
    st.session_state.selected_formats = ['mp4']

# ============================================
# 📦 HELPER FUNCTIONS
# ============================================

def execute_editing(video_path, actions, music_file=None, formats=None):
    """تنفيذ التعديلات مع دعم تصدير متعدد الصيغ."""
    err = media_engine.validate_actions(actions, video_path)
    if err:
        st.error(f"⚠️ {err}")
        return
    
    try:
        with st.spinner("🚀 جاري المونتاج... قد يستغرق دقائق"):
            clip = VideoFileClip(video_path)
            final = media_engine.apply_edit_actions(clip, actions, music_file)
            
            if formats and len(formats) > 1:
                results = media_engine.export_multiple_formats(final, formats)
                st.success("✅ تم التصدير بعدة صيغ!")
                for fmt, path in results.items():
                    if path:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.video(path)
                        with col2:
                            st.metric(f"📁 {fmt.upper()}", f"{os.path.getsize(path) / (1024*1024):.1f} MB")
            else:
                fmt = formats[0] if formats else "mp4"
                out = media_engine.export_video(final, format=fmt)
                st.video(out)
                st.success(f"✅ تم التصدير بنجاح!")
                st.caption(f"📁 الملف: {os.path.basename(out)}")
            
            # حفظ في Undo/Redo
            st.session_state.undo_redo_manager.add_state(video_path, actions, music_file)
            
            # تنظيف الذاكرة
            clip.close()
            final.close()
            st.session_state.ai_result = None
            st.session_state.waiting_confirmation = False
            st.balloons()
            
    except Exception as e:
        st.error(f"❌ خطأ: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def render_header():
    """عرض الهيدر الفرعوني."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="margin: 0;">🏛️ المونتير الفرعوني 🏛️</h1>
            <p style="color: var(--nile-turquoise); font-size: 1.2rem; margin: 0.5rem 0;">
                AI Video Editor - Powered by Ancient Egyptian Magic
            </p>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# 🏛️ SIDEBAR - القائمة المختصرة
# ============================================
with st.sidebar:
    st.markdown("### 🎛️ إعدادات متقدمة")
    
    # AI Status
    try:
        ai_engine.configure_ai()
        st.success("✅ AI متصل")
    except:
        st.error("❌ خطأ في API")
    
    st.markdown("---")
    
    # Quick Stats Toggle
    if st.checkbox("📊 إظهار الإحصائيات", value=st.session_state.show_stats):
        st.session_state.show_stats = True
        try:
            stats = command_cache.get_usage_stats()
            st.metric("أوامر محفوظة", stats['unique'])
            st.metric("توكينز موفرة", f"{stats['saved_tokens']}+")
        except:
            st.warning("لا توجد إحصائيات")
    else:
        st.session_state.show_stats = False
    
    st.markdown("---")
    
    # Cache Settings
    with st.expander("⚙️ إعدادات الذاكرة"):
        st.session_state.cache_threshold = st.slider(
            "حساسية التطابق",
            0.5, 1.0, 
            st.session_state.cache_threshold,
            0.05
        )
        if st.button("🗑️ مسح الذاكرة"):
            command_cache.clear_cache()
            st.success("تم المسح!")
            time.sleep(1)
            st.rerun()
    
    # Export/Import
    with st.expander("💾 نسخ احتياطي"):
        json_data = command_cache.export_db_to_json()
        st.download_button(
            "📥 تحميل Backup",
            data=json_data,
            file_name=f"backup_{time.strftime('%Y%m%d')}.json",
            mime="application/json"
        )
        
        uploaded = st.file_uploader("📤 استعادة", type=["json"])
        if uploaded:
            count = command_cache.import_db_from_json(uploaded.getvalue().decode())
            st.success(f"تم استعادة {count} أمر!")
            time.sleep(1)
            st.rerun()
    
    st.markdown("---")
    
    # Reset Button
    if st.button("🔄 مشروع جديد", type="primary", use_container_width=True):
        st.session_state.clear()
        st.session_state.undo_redo_manager = undo_redo.UndoRedoManager()
        st.rerun()

# ============================================
# 📺 MAIN LAYOUT - التصميم الرئيسي
# ============================================

# Header
render_header()

# Main Container
main_container = st.container()

with main_container:
    # ────────────────────────────────────────
    # 🎬 SECTION 1: Video Upload & Player
    # ────────────────────────────────────────
    st.markdown("### 📂 رفع الفيديو")
    
    uploaded_file = st.file_uploader(
        "اسحب الفيديو هنا أو اضغط للاختيار",
        type=["mp4", "mov", "avi"],
        help="الصيغ المدعومة: MP4, MOV, AVI"
    )
    
    if uploaded_file:
        temp_path = media_engine.save_uploaded_file(uploaded_file)
        st.session_state.current_video_path = temp_path
        
        # Video Player + Info
        col_video, col_info = st.columns([3, 1])
        
        with col_video:
            st.markdown("#### 📺 معاينة الفيديو")
            st.video(temp_path)
        
        with col_info:
            st.markdown("#### 📋 معلومات الملف")
            file_size = os.path.getsize(temp_path) / (1024 * 1024)
            st.metric("الحجم", f"{file_size:.1f} MB")
            
            try:
                with VideoFileClip(temp_path) as clip:
                    duration = clip.duration
                    st.metric("المدة", f"{int(duration // 60)}:{int(duration % 60):02d}")
                    st.metric("الأبعاد", f"{clip.w}×{clip.h}")
                    st.metric("FPS", f"{clip.fps:.1f}")
            except:
                st.warning("تعذر قراءة المعلومات")
        
        # ────────────────────────────────────────
        # 🎞️ SECTION 2: Timeline
        # ────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🎞️ خط الزمن (Timeline)")
        
        with st.spinner("⏳ جاري تحميل الفريمات..."):
            frames = media_engine.extract_timeline_frames(temp_path, num_frames=10)
            if frames:
                try:
                    st.markdown(
                        ui_utils.render_timeline_html(frames, video_id="main"),
                        unsafe_allow_html=True
                    )
                except:
                    ui_utils.render_timeline_streamlit(frames)
        
        # ────────────────────────────────────────
        # 🎚️ SECTION 3: Controls & Commands
        # ────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🎚️ لوحة التحكم")
        
        # Tabs for Input Methods
        tab_voice, tab_text, tab_templates, tab_batch = st.tabs([
            "🎤 الصوت",
            "⌨️ النص",
            "📑 القوالب",
            "📦 معالجة متعددة"
        ])
        
        # ─── TAB 1: Voice ───
        with tab_voice:
            st.info("🎤 سجّل أمرك صوتياً (مثلاً: قص أول 10 ثواني)")
            
            col_rec, col_music = st.columns(2)
            
            with col_rec:
                audio = audiorecorder("اضغط للتسجيل", "جاري التسجيل...")
                if len(audio) > 0:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as fp:
                        audio.export(fp.name, format="wav")
                        audio_path = fp.name
                    st.audio(audio_path)
                    
                    if st.button("🧠 تحليل الأمر الصوتي", type="primary", use_container_width=True):
                        with st.spinner("جاري الفهم..."):
                            result = ai_engine.analyze_command(
                                audio_path=audio_path,
                                cache_threshold=st.session_state.cache_threshold
                            )
                            if result:
                                st.session_state.ai_result = result
                                st.session_state.waiting_confirmation = True
                                st.rerun()
            
            with col_music:
                st.markdown("#### 🎵 موسيقى خلفية (اختياري)")
                music = st.file_uploader("ارفع ملف صوتي", type=["mp3", "wav"], key="music_voice")
                if music:
                    st.session_state.music_path = media_engine.save_uploaded_file(music)
                    st.audio(st.session_state.music_path)
                    st.success("✅ جاهز!")
        
        # ─── TAB 2: Text ───
        with tab_text:
            st.info("⌨️ اكتب أمرك نصياً")
            
            col_txt, col_music2 = st.columns(2)
            
            with col_txt:
                user_text = st.text_area(
                    "أمر التعديل:",
                    placeholder="مثال: قص من 5 ثواني إلى 15 ثانية وحول لأبيض وأسود",
                    height=100
                )
                
                if st.button("🧠 تحليل النص", type="primary", use_container_width=True) and user_text:
                    with st.spinner("جاري الفهم..."):
                        result = ai_engine.analyze_command(
                            text_prompt=user_text,
                            cache_threshold=st.session_state.cache_threshold
                        )
                        if result:
                            st.session_state.ai_result = result
                            st.session_state.waiting_confirmation = True
                            st.rerun()
            
            with col_music2:
                st.markdown("#### 🎵 موسيقى خلفية (اختياري)")
                music2 = st.file_uploader("ارفع ملف صوتي", type=["mp3", "wav"], key="music_text")
                if music2:
                    st.session_state.music_path = media_engine.save_uploaded_file(music2)
                    st.audio(st.session_state.music_path)
                    st.success("✅ جاهز!")
        
        # ─── TAB 3: Templates ───
        with tab_templates:
            templates = command_cache.get_all_templates()
            
            if templates:
                st.info("📑 اختر قالباً جاهزاً أو أنشئ واحداً جديداً")
                
                col_select, col_actions = st.columns([2, 1])
                
                with col_select:
                    template_names = [t['name'] for t in templates]
                    selected = st.selectbox("القوالب المتاحة:", template_names)
                    
                    if selected:
                        tmpl = next(t for t in templates if t['name'] == selected)
                        st.caption(f"📝 الوصف: {tmpl.get('description', 'لا يوجد')}")
                        with st.expander("عرض الخطوات"):
                            st.json(tmpl['actions'])
                
                with col_actions:
                    st.markdown("#### إجراءات")
                    if st.button("🚀 تطبيق", type="primary", use_container_width=True):
                        st.session_state.ai_result = {
                            'transcription': f"قالب: {selected}",
                            'actions': tmpl['actions'],
                            'source': 'قالب جاهز'
                        }
                        st.session_state.waiting_confirmation = True
                        st.rerun()
                    
                    if st.button("🗑️ حذف", type="secondary", use_container_width=True):
                        command_cache.delete_template(selected)
                        st.success("تم الحذف!")
                        time.sleep(0.5)
                        st.rerun()
            else:
                st.warning("لا توجد قوالب محفوظة. قم بإنشاء واحد بعد تنفيذ أمر!")
        
        # ─── TAB 4: Batch ───
        with tab_batch:
            st.info("📦 معالجة عدة فيديوهات بنفس الأمر")
            
            batch_files = st.file_uploader(
                "ارفع عدة فيديوهات",
                type=["mp4", "mov"],
                accept_multiple_files=True
            )
            
            if batch_files and st.session_state.ai_result:
                st.success(f"تم رفع {len(batch_files)} فيديو")
                
                if st.button("🚀 معالجة الكل", type="primary", use_container_width=True):
                    video_paths = [media_engine.save_uploaded_file(f) for f in batch_files]
                    actions = st.session_state.ai_result['actions']
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(current, total):
                        progress_bar.progress(current / total)
                        status_text.text(f"معالجة {current}/{total}...")
                    
                    results = batch_processor.batch_process(
                        video_paths,
                        actions,
                        st.session_state.music_path,
                        progress_callback=update_progress
                    )
                    
                    success_count = sum(1 for r in results if r['status'] == 'success')
                    st.success(f"✅ تمت معالجة {success_count}/{len(results)} فيديو!")
                    
                    for r in results:
                        if r['status'] == 'success':
                            st.video(r['output'])
                        else:
                            st.error(f"❌ {os.path.basename(r['input'])}: {r.get('error', 'خطأ')}")
            elif batch_files:
                st.warning("قم بتحليل أمر أولاً في تبويب الصوت أو النص")
        
        # ────────────────────────────────────────
        # 🎯 SECTION 4: Results & Actions
        # ────────────────────────────────────────
        if st.session_state.ai_result:
            st.markdown("---")
            st.markdown("### 🎯 نتيجة التحليل")
            
            result = st.session_state.ai_result
            
            # Header Info
            col_source, col_undo, col_redo = st.columns([2, 1, 1])
            
            with col_source:
                source = result.get('source', '')
                if result.get('from_cache'):
                    st.success(f"💾 من الذاكرة (توفير {int(result.get('similarity', 0) * 100)}%)")
                elif source:
                    st.info(f"📋 المصدر: {source}")
                else:
                    st.info("🤖 معالج بالذكاء الاصطناعي")
            
            with col_undo:
                if st.button("⏪ تراجع", disabled=not st.session_state.undo_redo_manager.can_undo()):
                    prev = st.session_state.undo_redo_manager.undo()
                    if prev:
                        st.session_state.ai_result = {'actions': prev['actions']}
                        st.rerun()
            
            with col_redo:
                if st.button("⏩ إعادة", disabled=not st.session_state.undo_redo_manager.can_redo()):
                    next_state = st.session_state.undo_redo_manager.redo()
                    if next_state:
                        st.session_state.ai_result = {'actions': next_state['actions']}
                        st.rerun()
            
            # Transcription
            st.markdown(f"**🗣️ فهمت:** {result.get('transcription', 'أمر مباشر')}")
            
            # Actions Display
            with st.expander("📋 الخطوات المطلوبة", expanded=True):
                st.json(result['actions'])
            
            # Quick Actions
            col_preview, col_save, col_export = st.columns(3)
            
            with col_preview:
                if st.button("👁️ معاينة سريعة", use_container_width=True):
                    st.session_state.preview_mode = True
                    with st.spinner("جاري إنشاء المعاينة..."):
                        previews = preview_engine.preview_all_steps(
                            temp_path,
                            result['actions'],
                            preview_duration=5.0,
                            music_path=st.session_state.music_path
                        )
                        for p in previews:
                            st.caption(f"خطوة {p['step_index']+1}: {p['action']}")
                            st.video(p['preview_path'])
            
            with col_save:
                with st.popover("💾 حفظ كقالب"):
                    tmpl_name = st.text_input("اسم القالب:")
                    tmpl_desc = st.text_input("وصف (اختياري):")
                    if st.button("حفظ") and tmpl_name:
                        command_cache.save_template(tmpl_name, result['actions'], tmpl_desc)
                        st.success("تم!")
                        time.sleep(1)
                        st.rerun()
            
            with col_export:
                st.session_state.selected_formats = st.multiselect(
                    "📤 صيغ التصدير",
                    ["mp4", "webm", "gif"],
                    default=st.session_state.selected_formats
                )
            
            # Warning Messages
            if any(a['action'] == 'music' for a in result['actions']) and not st.session_state.music_path:
                st.warning("⚠️ الأمر يتطلب موسيقى! ارفع ملف صوتي في تبويب الصوت/النص")
            
            # Confirmation Area
            st.markdown("---")
            st.markdown("### ✅ تأكيد التنفيذ")
            
            if st.session_state.waiting_confirmation:
                col_confirm, col_cancel = st.columns(2)
                
                with col_confirm:
                    if st.button("✅ تنفيذ الآن", type="primary", use_container_width=True):
                        execute_editing(
                            temp_path,
                            result['actions'],
                            st.session_state.music_path,
                            st.session_state.selected_formats
                        )
                
                with col_cancel:
                    if st.button("❌ إلغاء", type="secondary", use_container_width=True):
                        st.session_state.ai_result = None
                        st.session_state.waiting_confirmation = False
                        st.rerun()

# ============================================
# 🏛️ FOOTER
# ============================================
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption("🏛️ Egyptian Pharaoh Theme")
with footer_col2:
    st.caption("💻 Made with ❤️ for Mummia3d")
with footer_col3:
    st.caption("⚡ Powered by Claude AI")

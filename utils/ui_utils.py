import streamlit as st
import base64
from io import BytesIO
from PIL import Image

def load_css(file_name: str):
    """Loads external CSS file with UTF-8 encoding."""
    try:
        with open(file_name, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Error: CSS file '{file_name}' not found.")

def image_to_base64(img: Image.Image) -> str:
    """Converts PIL Image to Base64 string."""
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def render_timeline_html(frames: list, video_id: str = "main_video") -> str:
    """Generates HTML for the visual timeline with interactive click."""
    if not frames:
        return '<p>لا توجد فريمات لعرضها.</p>'
    
    # بداية الحاوية
    html_content = f'<div class="timeline-wrapper"><div class="timeline-container" id="timeline-{video_id}">'
    
    for t, img in frames:
        try:
            img_str = image_to_base64(img)
            # إضافة onclick للانتقال للوقت المحدد
            # ملاحظة: نمرر الوقت t فقط للدالة
            html_content += f'''<div class="frame-box" onclick="seekToTime({t})" style="cursor: pointer;">
            <img src="data:image/jpeg;base64,{img_str}" class="timeline-img" alt="Frame at {int(t)}s">
            <span class="time-badge">{int(t)}s</span>
        </div>'''
        except Exception as e:
            continue
    
    # إضافة JavaScript للانتقال للوقت (النسخة الذكية)
    # هذه النسخة تبحث عن أول فيديو في الصفحة، مما يحل مشكلة تغير الـ ID
    html_content += '</div></div>'
    html_content += '''
    <script>
    function seekToTime(time) {
        // البحث عن أول عنصر فيديو HTML5 في الصفحة
        const videos = document.getElementsByTagName('video');
        if (videos.length > 0) {
            const video = videos[0];
            video.currentTime = time;
            video.play();
            // إيقاف الفيديو بعد ثانية واحدة للمعاينة فقط
            setTimeout(() => video.pause(), 1000);
        } else {
            console.log("Video element not found!");
        }
    }
    </script>
    '''
    return html_content

def render_timeline_streamlit(frames: list):
    """Alternative: Render timeline using Streamlit native components (more reliable fallback)."""
    if not frames:
        st.warning("لا توجد فريمات لعرضها.")
        return
    
    # عرض الصور في أعمدة بجانب بعضها
    num_cols = len(frames)
    # نتأكد أن العدد لا يساوي صفر لتجنب الأخطاء
    if num_cols > 0:
        cols = st.columns(num_cols)
        for idx, (t, img) in enumerate(frames):
            with cols[idx]:
                st.image(img, use_container_width=True, caption=f"{int(t)}s")
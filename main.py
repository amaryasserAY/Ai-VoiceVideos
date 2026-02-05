import os
import json
import google.generativeai as genai
from moviepy.editor import VideoFileClip, vfx
from dotenv import load_dotenv

# 1. تحميل الإعدادات السرية
load_dotenv() # بيقرأ ملف .env تلقائياً
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("⚠️ مفتاح API غير موجود! تأكد من إنشاء ملف .env")

genai.configure(api_key=api_key)

# 2. دالة فهم الأوامر (AI Brain)
def get_edit_instructions(user_prompt):
    print("🤔 جاري تحليل طلبك...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    system_instruction = """
    You are a video editing assistant. Translate natural language commands into JSON.
    Supported actions:
    - trim (requires start_time, end_time in seconds)
    - mute (no params)
    - speed (requires factor e.g., 1.5, 2.0)
    - black_white (no params)
    
    Return ONLY raw JSON. No markdown.
    Example: {"action": "trim", "start": 0, "end": 10}
    """
    
    try:
        response = model.generate_content(f"{system_instruction}\n\nUser: {user_prompt}")
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"حدث خطأ في الذكاء الاصطناعي: {e}")
        return None

# 3. دالة التنفيذ (The Editor)
def execute_edit(video_path, instructions):
    if not instructions: return

    try:
        print(f"🎬 جاري تحميل الفيديو: {video_path}")
        clip = VideoFileClip(video_path)
        action = instructions.get("action")
        output_name = f"output_{action}.mp4"

        final_clip = clip # نسخة احتياطية

        if action == "trim":
            start = instructions.get("start", 0)
            end = instructions.get("end", clip.duration)
            final_clip = clip.subclip(start, end)
            print(f"✂️ قص الفيديو: من {start} إلى {end}")

        elif action == "mute":
            final_clip = clip.without_audio()
            print("🔇 تم كتم الصوت.")

        elif action == "speed":
            factor = instructions.get("factor", 1.0)
            final_clip = clip.fx(vfx.speedx, factor)
            print(f"⏩ تم تغيير السرعة: {factor}x")

        elif action == "black_white":
            final_clip = clip.fx(vfx.blackwhite)
            print("🎨 تم تطبيق فلتر أبيض وأسود.")
        
        else:
            print("⚠️ أمر غير معروف.")
            return

        print("💾 جاري الحفظ... (قد يستغرق وقتاً حسب حجم الفيديو)")
        final_clip.write_videofile(output_name, codec='libx264', audio_codec='aac', logger=None)
        print(f"✅ تم! الفيديو محفوظ باسم: {output_name}")

    except Exception as e:
        print(f"❌ خطأ أثناء المعالجة: {e}")

# --- منطقة التشغيل ---
if __name__ == "__main__":
    # تأكد من وجود ملف فيديو باسم input.mp4 في نفس المجلد
    video_file = "input.mp4"
    
    if os.path.exists(video_file):
        command = input("🎤 اكتب أمر التعديل (مثلاً: قص اول 5 ثواني): ")
        
        instructions = get_edit_instructions(command)
        if instructions:
            print(f"📝 الأمر المترجم: {instructions}")
            execute_edit(video_file, instructions)
    else:
        print(f"⚠️ الملف {video_file} غير موجود. يرجى وضع فيديو للتجربة.")
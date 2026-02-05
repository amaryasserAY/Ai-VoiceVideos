"""
نظام Preview: معاينة سريعة لكل خطوة قبل التنفيذ الكامل.
"""
import tempfile
from moviepy.editor import VideoFileClip, vfx, AudioFileClip, CompositeAudioClip, afx
from . import media_engine

def preview_step(video_path: str, actions: list, step_index: int, preview_duration: float = 5.0, music_path: str = None) -> str:
    """
    معاينة خطوة واحدة من التعديلات.
    يرجع مسار ملف فيديو Preview قصير (5 ثواني).
    """
    try:
        clip = VideoFileClip(video_path)
        original_duration = clip.duration
        
        # تطبيق الخطوات حتى step_index
        for i, step in enumerate(actions[:step_index + 1]):
            action = step.get("action")
            
            if action == "trim":
                start = float(step.get("start", 0))
                end = float(step.get("end", clip.duration))
                if end > clip.duration: end = clip.duration
                clip = clip.subclip(start, end)
                
            elif action == "mute":
                clip = clip.without_audio()
                
            elif action == "speed":
                factor = float(step.get("factor", 1.0))
                clip = clip.fx(vfx.speedx, factor)
                
            elif action == "black_white":
                clip = clip.fx(vfx.blackwhite)
        
        # تطبيق الموسيقى إذا كانت موجودة في الخطوات المطبقة
        music_action = next((x for x in actions[:step_index + 1] if x.get("action") == "music"), None)
        if music_action and music_path:
            try:
                bg_music = AudioFileClip(music_path)
                bg_volume = float(music_action.get("volume", 0.3))
                bg_music = bg_music.volumex(bg_volume)
                
                if bg_music.duration < clip.duration:
                    bg_music = afx.audio_loop(bg_music, duration=clip.duration)
                else:
                    bg_music = bg_music.subclip(0, clip.duration)
                
                final_audio = CompositeAudioClip([clip.audio, bg_music]) if clip.audio else bg_music
                clip = clip.set_audio(final_audio)
            except Exception:
                pass
        
        # قص Preview (5 ثواني من البداية أو كل الفيديو إذا كان أقصر)
        preview_clip = clip.subclip(0, min(preview_duration, clip.duration))
        
        # تصدير Preview
        preview_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
        preview_clip.write_videofile(preview_path, codec='libx264', audio_codec='aac', logger=None, verbose=False)
        
        clip.close()
        preview_clip.close()
        
        return preview_path
    except Exception as e:
        print(f"Preview error: {e}")
        return None

def preview_all_steps(video_path: str, actions: list, preview_duration: float = 5.0, music_path: str = None) -> list:
    """
    معاينة كل الخطوات واحدة تلو الأخرى.
    يرجع قائمة بمسارات ملفات Preview.
    """
    previews = []
    for i in range(len(actions)):
        preview_path = preview_step(video_path, actions, i, preview_duration, music_path)
        if preview_path:
            previews.append({
                'step_index': i,
                'action': actions[i].get('action'),
                'preview_path': preview_path
            })
    return previews

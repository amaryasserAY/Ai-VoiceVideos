import os
import tempfile
import time
import numpy as np
from PIL import Image
from moviepy.editor import VideoFileClip, vfx, AudioFileClip, CompositeAudioClip, afx
from moviepy.video.fx.all import crop
from . import subtitle_engine
from .config import OUTPUT_DIR

def save_uploaded_file(uploaded_file) -> str:
    """Saves uploaded Streamlit file to temp disk."""
    try:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        print(f"File save error: {e}")
        return None

def extract_timeline_frames(video_path: str, num_frames: int = 8, max_duration: float = 300.0) -> list:
    """
    Extracts thumbnails from video at equal intervals.
    ✅ FIXED: Uses context manager to prevent memory leaks.
    """
    frames = []
    try:
        with VideoFileClip(video_path) as clip:
            duration = clip.duration
            
            if duration <= 0:
                return []
            
            effective_duration = min(duration, max_duration)
            if duration > max_duration:
                num_frames = min(num_frames, int(effective_duration / 10))
            
            times = np.linspace(0, max(0, effective_duration - 0.1), 
                              min(num_frames, int(effective_duration) + 1))
            
            for t in times:
                try:
                    frame = clip.get_frame(t)
                    img = Image.fromarray(frame)
                    img.thumbnail((150, 150))
                    frames.append((t, img))
                except:
                    continue
        
        return frames
    except Exception as e:
        print(f"Timeline error: {e}")
        return []

def validate_actions(actions: list, video_path: str = None) -> str:
    """التحقق من صحة الأوامر."""
    if not actions:
        return ""
    
    for i, step in enumerate(actions):
        action = step.get("action")
        
        if action == "trim":
            start = float(step.get("start", 0))
            end = float(step.get("end", 0))
            if start < 0 or (end > 0 and end <= start):
                return f"خطأ في القص: التوقيت غير منطقي."
        
        elif action == "crop":
            ar = step.get("aspect_ratio")
            if ar and ar not in ["9:16", "16:9", "1:1"]:
                return f"الأبعاد {ar} غير مدعومة حالياً."
    
    return ""

def apply_edit_actions(clip: VideoFileClip, actions: list, music_path: str = None) -> VideoFileClip:
    """
    Applies JSON actions including Rotate, Crop, Volume.
    
    Note: This function modifies the clip in-place and returns it.
    The caller is responsible for closing the final clip.
    """
    # 1. تطبيق التعديلات البصرية والزمنية
    for step in actions:
        action = step.get("action")
        
        if action == "trim":
            start = float(step.get("start", 0))
            end = float(step.get("end", clip.duration))
            if end > clip.duration:
                end = clip.duration
            clip = clip.subclip(start, end)
            
        elif action == "mute":
            clip = clip.without_audio()
            
        elif action == "volume":
            vol = float(step.get("level", 1.0))
            clip = clip.volumex(vol)

        elif action == "speed":
            factor = float(step.get("factor", 1.0))
            clip = clip.fx(vfx.speedx, factor)
            
        elif action == "rotate":
            angle = int(step.get("angle", 90))
            clip = clip.rotate(angle)

        elif action == "crop":
            ratio = step.get("aspect_ratio", "9:16")
            w, h = clip.size
            
            if ratio == "9:16":
                target_ratio = 9/16
                new_w = h * target_ratio
                if new_w <= w:
                    x1 = (w / 2) - (new_w / 2)
                    clip = crop(clip, x1=x1, y1=0, width=new_w, height=h)
                else:
                    new_h = w / target_ratio
                    y1 = (h / 2) - (new_h / 2)
                    clip = crop(clip, x1=0, y1=y1, width=w, height=new_h)
            
            elif ratio == "1:1":
                min_dim = min(w, h)
                x1 = (w / 2) - (min_dim / 2)
                y1 = (h / 2) - (min_dim / 2)
                clip = crop(clip, x1=x1, y1=y1, width=min_dim, height=min_dim)
                
            elif ratio == "16:9":
                target_ratio = 16/9
                new_h = w / target_ratio
                if new_h <= h:
                    y1 = (h / 2) - (new_h / 2)
                    clip = crop(clip, x1=0, y1=y1, width=w, height=new_h)

        elif action == "black_white":
            clip = clip.fx(vfx.blackwhite)

    # 2. تطبيق Subtitles
    subtitle_actions = [s for s in actions if s.get("action") == "subtitle"]
    if subtitle_actions:
        subtitles = []
        for sub_action in subtitle_actions:
            subtitles.append({
                'text': sub_action.get('text', ''),
                'start': float(sub_action.get('start', 0)),
                'end': float(sub_action.get('end', 0)),
                'position': sub_action.get('position', 'bottom'),
                'fontsize': sub_action.get('fontsize', 50),
                'color': sub_action.get('color', 'white'),
                'bg_color': sub_action.get('bg_color', 'black')
            })
        clip = subtitle_engine.add_subtitles(clip, subtitles)

    # 3. تطبيق الموسيقى الخلفية
    music_action = next((x for x in actions if x.get("action") == "music"), None)
    if music_action and music_path:
        background_music = None
        try:
            background_music = AudioFileClip(music_path)
            bg_volume = float(music_action.get("volume", 0.3))
            background_music = background_music.volumex(bg_volume)
            
            if background_music.duration < clip.duration:
                background_music = afx.audio_loop(background_music, duration=clip.duration)
            else:
                background_music = background_music.subclip(0, clip.duration)
                
            final_audio = CompositeAudioClip([clip.audio, background_music]) if clip.audio else background_music
            clip = clip.set_audio(final_audio)
        except Exception as e:
            print(f"Music Error: {e}")
        finally:
            # تنظيف AudioFileClip
            if background_music:
                background_music.close()

    return clip

def export_video(clip: VideoFileClip, output_dir: str = None, format: str = "mp4") -> str:
    """
    Exports the final video.
    ✅ FIXED: Uses config.py for output directory.
    """
    if output_dir is None:
        output_dir = str(OUTPUT_DIR)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    
    if format == "gif":
        output_path = os.path.join(output_dir, f"video_{timestamp}.gif")
        clip.write_gif(output_path, logger=None)
    elif format == "webm":
        output_path = os.path.join(output_dir, f"video_{timestamp}.webm")
        clip.write_videofile(output_path, codec='libvpx-vp9', audio_codec='libvorbis', logger=None)
    else:
        output_path = os.path.join(output_dir, f"video_{timestamp}.mp4")
        clip.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None)
        
    return output_path

def export_multiple_formats(clip: VideoFileClip, formats: list = ["mp4"], output_dir: str = None) -> dict:
    """
    Export video in multiple formats.
    """
    results = {}
    for fmt in formats:
        try:
            results[fmt] = export_video(clip, output_dir, fmt)
        except Exception as e:
            print(f"Export error for {fmt}: {e}")
            results[fmt] = None
    return results

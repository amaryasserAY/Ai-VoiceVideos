"""
نظام Subtitles: إضافة نص على الفيديو.
"""
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from typing import List, Dict

def add_subtitle(clip: VideoFileClip, text: str, start_time: float, end_time: float,
                 position: str = 'bottom', fontsize: int = 50, color: str = 'white',
                 bg_color: str = 'black', font: str = 'Arial-Bold') -> VideoFileClip:
    """
    إضافة subtitle واحد على الفيديو.
    
    Args:
        clip: الفيديو
        text: النص
        start_time: وقت البداية (ثواني)
        end_time: وقت النهاية (ثواني)
        position: 'top', 'bottom', 'center'
        fontsize: حجم الخط
        color: لون النص
        bg_color: لون الخلفية
        font: نوع الخط
    """
    try:
        # تحديد الموضع
        if position == 'top':
            pos = ('center', 50)
        elif position == 'bottom':
            pos = ('center', clip.h - 100)
        else:
            pos = ('center', 'center')
        
        # إنشاء TextClip
        txt_clip = TextClip(
            text,
            fontsize=fontsize,
            color=color,
            font=font,
            bg_color=bg_color,
            size=(clip.w * 0.9, None),
            method='caption'
        ).set_position(pos).set_duration(end_time - start_time).set_start(start_time)
        
        # دمج النص مع الفيديو
        final = CompositeVideoClip([clip, txt_clip])
        return final
    except Exception as e:
        print(f"Subtitle error: {e}")
        return clip

def add_subtitles(clip: VideoFileClip, subtitles: List[Dict]) -> VideoFileClip:
    """
    إضافة عدة subtitles.
    
    subtitles format:
    [
        {"text": "مرحبا", "start": 0, "end": 5, "position": "bottom"},
        ...
    ]
    """
    result_clip = clip
    for sub in subtitles:
        result_clip = add_subtitle(
            result_clip,
            sub.get('text', ''),
            float(sub.get('start', 0)),
            float(sub.get('end', 0)),
            sub.get('position', 'bottom'),
            sub.get('fontsize', 50),
            sub.get('color', 'white'),
            sub.get('bg_color', 'black'),
            sub.get('font', 'Arial-Bold')
        )
    return result_clip

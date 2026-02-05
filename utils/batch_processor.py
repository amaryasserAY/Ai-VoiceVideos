"""
Batch Processing: معالجة عدة فيديوهات بنفس الأوامر.
"""
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Callable
from moviepy.editor import VideoFileClip
from . import media_engine

def process_single_video(video_path: str, actions: List[Dict], music_path: str = None, output_dir: str = "My_Produced_Videos") -> Dict:
    """معالجة فيديو واحد."""
    try:
        clip = VideoFileClip(video_path)
        final_clip = media_engine.apply_edit_actions(clip, actions, music_path)
        output_path = media_engine.export_video(final_clip, output_dir)
        
        clip.close()
        final_clip.close()
        
        return {
            'input': video_path,
            'output': output_path,
            'status': 'success'
        }
    except Exception as e:
        return {
            'input': video_path,
            'output': None,
            'status': 'error',
            'error': str(e)
        }

def batch_process(video_paths: List[str], actions: List[Dict], music_path: str = None, 
                  max_workers: int = 2, progress_callback: Callable = None) -> List[Dict]:
    """
    معالجة عدة فيديوهات بشكل متوازي.
    
    Args:
        video_paths: قائمة بمسارات الفيديوهات
        actions: قائمة الأوامر
        music_path: مسار الموسيقى (اختياري)
        max_workers: عدد العمال المتوازيين (افتراضي 2)
        progress_callback: دالة callback للتقدم (current, total)
    
    Returns:
        قائمة بنتائج المعالجة
    """
    results = []
    total = len(video_paths)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # إرسال المهام
        futures = {
            executor.submit(process_single_video, path, actions, music_path): path
            for path in video_paths
        }
        
        # جمع النتائج
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            
            if progress_callback:
                progress_callback(completed, total)
    
    return results

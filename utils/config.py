"""
نظام إدارة المسارات والإعدادات - متوافق مع PyInstaller.
يضمن عمل البرنامج في بيئة التطوير وبعد التحويل لـ .exe
"""
import sys
import os
import shutil
from pathlib import Path
from typing import Dict, Optional

# ==================== Path Resolution ====================

def get_base_path() -> Path:
    """
    الحصول على المسار الأساسي للبرنامج.
    - في التطوير: مجلد المشروع
    - في .exe: المجلد المؤقت الذي يفك فيه PyInstaller الملفات
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return Path(sys._MEIPASS)
    else:
        # Running in normal Python environment
        # نرجع مسار المشروع (مجلد utils/..)
        return Path(__file__).parent.parent

def get_data_dir() -> Path:
    """
    الحصول على مجلد بيانات المستخدم.
    - في التطوير: نفس مجلد المشروع
    - في .exe: AppData/Roaming/AIVideoEditor (Windows)
    """
    if getattr(sys, 'frozen', False):
        # Store user data in AppData on Windows
        if sys.platform == 'win32':
            app_data = Path(os.getenv('APPDATA', os.path.expanduser('~'))) / 'AIVideoEditor'
        else:
            # Linux/Mac
            app_data = Path.home() / '.aivideoeditor'
        
        # إنشاء المجلد إذا لم يكن موجود
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data
    else:
        # في بيئة التطوير، نستخدم مجلد المشروع
        return get_base_path()

def get_output_dir() -> Path:
    """مجلد حفظ الفيديوهات المصدرة."""
    output = get_data_dir() / "My_Produced_Videos"
    output.mkdir(parents=True, exist_ok=True)
    return output

def get_temp_dir() -> Path:
    """مجلد الملفات المؤقتة."""
    temp = get_data_dir() / "temp"
    temp.mkdir(parents=True, exist_ok=True)
    return temp

# ==================== File Paths ====================

BASE_DIR = get_base_path()
DATA_DIR = get_data_dir()
OUTPUT_DIR = get_output_dir()
TEMP_DIR = get_temp_dir()

# Database files
DB_CACHE_PATH = DATA_DIR / "command_cache.db"
DB_SESSIONS_PATH = DATA_DIR / "sessions.db"

# CSS file (في المشروع)
CSS_FILE = BASE_DIR / "style.css"

# FFmpeg paths
FFMPEG_EXE = BASE_DIR / "ffmpeg.exe"
FFPROBE_EXE = BASE_DIR / "ffprobe.exe"

# ==================== Dependency Validation ====================

def check_ffmpeg() -> bool:
    """
    التحقق من وجود FFmpeg.
    يبحث في:
    1. نفس مجلد البرنامج (ffmpeg.exe)
    2. متغيرات النظام (PATH)
    """
    # أولاً: نبحث في مجلد البرنامج
    if FFMPEG_EXE.exists():
        # نضيف المسار لـ PATH حتى MoviePy تلقاه
        os.environ['PATH'] = str(BASE_DIR) + os.pathsep + os.environ.get('PATH', '')
        return True
    
    # ثانياً: نبحث في PATH
    return shutil.which('ffmpeg') is not None

def check_imagemagick() -> bool:
    """
    التحقق من وجود ImageMagick (اختياري - للـ Subtitles).
    """
    return shutil.which('magick') is not None or shutil.which('convert') is not None

def validate_dependencies() -> Dict[str, bool]:
    """
    فحص جميع المتطلبات الخارجية.
    
    Returns:
        dict: {'ffmpeg': True/False, 'imagemagick': True/False}
    """
    return {
        'ffmpeg': check_ffmpeg(),
        'imagemagick': check_imagemagick()
    }

def get_ffmpeg_path() -> Optional[str]:
    """الحصول على المسار الكامل لـ FFmpeg."""
    if FFMPEG_EXE.exists():
        return str(FFMPEG_EXE)
    return shutil.which('ffmpeg')

# ==================== Configuration Settings ====================

def get_settings_file() -> Path:
    """ملف الإعدادات (JSON)."""
    return DATA_DIR / "settings.json"

def load_settings() -> dict:
    """تحميل الإعدادات من الملف."""
    settings_file = get_settings_file()
    if settings_file.exists():
        try:
            import json
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # الإعدادات الافتراضية
    return {
        'cache_threshold': 0.85,
        'max_workers': 2,
        'default_output_format': 'mp4',
        'language': 'ar'
    }

def save_settings(settings: dict) -> bool:
    """حفظ الإعدادات."""
    try:
        import json
        settings_file = get_settings_file()
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

# ==================== Auto-Configuration ====================

def setup_environment():
    """
    إعداد البيئة تلقائياً عند استيراد الوحدة.
    - إضافة FFmpeg للـ PATH
    - إنشاء المجلدات المطلوبة
    """
    # إضافة FFmpeg للـ PATH
    if FFMPEG_EXE.exists():
        os.environ['PATH'] = str(BASE_DIR) + os.pathsep + os.environ.get('PATH', '')
    
    # إنشاء المجلدات
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

# تشغيل الإعداد التلقائي
setup_environment()

# ==================== Debug Info ====================

def print_config_info():
    """طباعة معلومات التكوين (للتطوير)."""
    print("=" * 50)
    print("📁 Configuration Info")
    print("=" * 50)
    print(f"Base Dir:     {BASE_DIR}")
    print(f"Data Dir:     {DATA_DIR}")
    print(f"Output Dir:   {OUTPUT_DIR}")
    print(f"Temp Dir:     {TEMP_DIR}")
    print(f"Cache DB:     {DB_CACHE_PATH}")
    print(f"Sessions DB:  {DB_SESSIONS_PATH}")
    print(f"FFmpeg:       {get_ffmpeg_path() or 'NOT FOUND'}")
    print(f"ImageMagick:  {'YES' if check_imagemagick() else 'NO'}")
    print("=" * 50)

# اختبار عند التشغيل المباشر
if __name__ == '__main__':
    print_config_info()

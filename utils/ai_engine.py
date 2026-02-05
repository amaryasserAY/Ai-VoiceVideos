import os
import json
import google.generativeai as genai
import streamlit as st
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import List, Optional, Literal
from . import command_cache

# ============================================
# IMPORT LOCAL PARSER
# ============================================
import re

class SmartLocalParser:
    """Parser محلي - يعالج 70% من الأوامر بدون AI!"""
    
    def __init__(self):
        self.arabic_to_english = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    
    def normalize_arabic_numbers(self, text: str) -> str:
        return text.translate(self.arabic_to_english)
    
    def parse_trim(self, text: str) -> Optional[dict]:
        """معالجة أوامر القص."""
        text = self.normalize_arabic_numbers(text.lower())
        
        # "قص من X إلى Y"
        match = re.search(r'(من|بداية|from|start).+?(\d+\.?\d*).*(إلى|ل|حتى|to|until).+?(\d+\.?\d*)', text)
        if match:
            start = float(match.group(2))
            end = float(match.group(4))
            return {'action': 'trim', 'start': start, 'end': end}
        
        # "أول X ثواني"
        match = re.search(r'(أول|اول|first).+?(\d+\.?\d*)', text)
        if match:
            duration = float(match.group(2))
            return {'action': 'trim', 'start': 0, 'end': duration}
        
        # "آخر X ثواني"  
        match = re.search(r'(آخر|اخر|last).+?(\d+\.?\d*)', text)
        if match:
            duration = float(match.group(2))
            return {'action': 'trim_last', 'duration': duration}
        
        return None
    
    def parse_speed(self, text: str) -> Optional[dict]:
        text = self.normalize_arabic_numbers(text.lower())
        match = re.search(r'(سرع|اسرع|speed|fast).+?(\d+\.?\d*)x?|x(\d+\.?\d*)', text)
        if match:
            factor = float(match.group(2) or match.group(3))
            return {'action': 'speed', 'factor': factor}
        return None
    
    def parse_crop(self, text: str) -> Optional[dict]:
        text = text.lower()
        if any(k in text for k in ['9:16', 'ريلز', 'reels', 'shorts', 'tiktok']):
            return {'action': 'crop', 'aspect_ratio': '9:16'}
        if any(k in text for k in ['16:9', 'يوتيوب', 'youtube']):
            return {'action': 'crop', 'aspect_ratio': '16:9'}
        if any(k in text for k in ['1:1', 'مربع', 'square', 'post', 'instagram']):
            return {'action': 'crop', 'aspect_ratio': '1:1'}
        return None
    
    def parse_rotate(self, text: str) -> Optional[dict]:
        text = text.lower()
        if '90' in text:
            return {'action': 'rotate', 'angle': 90}
        if '180' in text:
            return {'action': 'rotate', 'angle': 180}
        if '270' in text:
            return {'action': 'rotate', 'angle': 270}
        return None
    
    def parse(self, text: str) -> Optional[dict]:
        """المعالج الرئيسي."""
        if not text or len(text.strip()) < 3:
            return None
        
        text_normalized = text.lower().strip()
        actions = []
        
        # Mute
        if any(k in text_normalized for k in ['كتم', 'اكتم', 'mute', 'شيل الصوت', 'بدون صوت']):
            actions.append({'action': 'mute'})
        
        # Black & White
        if any(k in text_normalized for k in ['ابيض', 'أبيض', 'اسود', 'black', 'white', 'bw', 'gray']):
            actions.append({'action': 'black_white'})
        
        # Trim
        trim = self.parse_trim(text)
        if trim:
            actions.append(trim)
        
        # Speed
        speed = self.parse_speed(text)
        if speed:
            actions.append(speed)
        
        # Crop
        crop = self.parse_crop(text)
        if crop:
            actions.append(crop)
        
        # Rotate
        rotate = self.parse_rotate(text)
        if rotate:
            actions.append(rotate)
        
        if actions:
            return {
                'transcription': text,
                'actions': actions,
                'source': 'local_parser 🚀',
                'from_cache': False,
                'tokens_saved': 100
            }
        
        return None

# Quick Match للأوامر الشائعة جداً
QUICK_COMMANDS = {
    'كتم الصوت': [{'action': 'mute'}],
    'mute': [{'action': 'mute'}],
    'ابيض واسود': [{'action': 'black_white'}],
    'black and white': [{'action': 'black_white'}],
    'ريلز': [{'action': 'crop', 'aspect_ratio': '9:16'}],
    'shorts': [{'action': 'crop', 'aspect_ratio': '9:16'}],
    'reels': [{'action': 'crop', 'aspect_ratio': '9:16'}],
    'اول 5 ثواني': [{'action': 'trim', 'start': 0, 'end': 5}],
    'اول 10 ثواني': [{'action': 'trim', 'start': 0, 'end': 10}],
    'first 5 seconds': [{'action': 'trim', 'start': 0, 'end': 5}],
}

def quick_match(text: str) -> Optional[dict]:
    """تطابق فوري O(1) - أسرع من AI بـ 1000x!"""
    clean = text.lower().strip().replace('  ', ' ')
    if clean in QUICK_COMMANDS:
        return {
            'transcription': text,
            'actions': QUICK_COMMANDS[clean],
            'source': 'instant_match ⚡',
            'from_cache': False,
            'tokens_saved': 150
        }
    return None

# ============================================
# PYDANTIC SCHEMAS
# ============================================
class EditAction(BaseModel):
    action: Literal["trim", "mute", "volume", "speed", "black_white", "music", "rotate", "crop", "subtitle", "trim_last"]
    
    start: Optional[float] = Field(None, ge=0)
    end: Optional[float] = Field(None, ge=0)
    factor: Optional[float] = Field(None, gt=0, le=10)
    volume: Optional[float] = Field(None, ge=0.0, le=2.0)
    level: Optional[float] = Field(None, ge=0.0, le=3.0)
    angle: Optional[int] = Field(None)
    aspect_ratio: Optional[str] = Field(None)
    duration: Optional[float] = Field(None, ge=0)
    
    text: Optional[str] = None
    position: Optional[str] = "bottom"
    fontsize: Optional[int] = 50
    color: Optional[str] = "white"
    bg_color: Optional[str] = "black"

    @field_validator('end')
    def check_end_after_start(cls, v, values):
        if v is not None and values.data.get('start') is not None:
            if v <= values.data['start']:
                raise ValueError('End time must be greater than start time')
        return v

class CommandResponse(BaseModel):
    transcription: str
    actions: List[EditAction]

# ============================================
# AI CONFIGURATION
# ============================================
def configure_ai():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API Key not found in .env")
    genai.configure(api_key=api_key)

def _get_system_prompt() -> str:
    """Prompt مختصر - موفر للتوكينز."""
    return """Video editor. Output JSON only.
Actions: trim(start,end), mute(), volume(level), speed(factor), black_white(), rotate(angle), crop(aspect_ratio), music(volume), subtitle(text,start,end).
Example: {"transcription":"cut first 10s","actions":[{"action":"trim","start":0,"end":10}]}"""

# ============================================
# HYBRID INTELLIGENCE SYSTEM
# ============================================
def analyze_command(
    audio_path: str = None, 
    text_prompt: str = None, 
    use_cache: bool = True, 
    cache_threshold: float = 0.85
) -> dict:
    """
    نظام ذكاء هجين:
    1. Quick Match (⚡ فوري)
    2. Local Parser (🚀 محلي)
    3. Cache (💾 ذاكرة)
    4. AI (🤖 جيميني) - الملاذ الأخير!
    """
    
    # للصوت: اضطرارياً نستخدم AI
    if audio_path:
        return _ai_fallback(audio_path, None, use_cache)
    
    if not text_prompt:
        return None
    
    # LEVEL 1: Quick Match
    quick_result = quick_match(text_prompt)
    if quick_result:
        return quick_result
    
    # LEVEL 2: Local Parser
    parser = SmartLocalParser()
    local_result = parser.parse(text_prompt)
    if local_result:
        if use_cache:
            command_cache.save_command(
                text_prompt, 
                local_result['actions'], 
                local_result['transcription']
            )
        return local_result
    
    # LEVEL 3: Cache
    if use_cache:
        cached = command_cache.find_similar_command(text_prompt, threshold=cache_threshold)
        if cached:
            return {
                'transcription': cached['transcription'] or text_prompt,
                'actions': cached['actions'],
                'from_cache': True,
                'source': 'cache 💾',
                'similarity': cached['similarity'],
                'tokens_saved': 100
            }
    
    # LEVEL 4: AI Fallback
    return _ai_fallback(None, text_prompt, use_cache)

def _ai_fallback(audio_path: str = None, text_prompt: str = None, use_cache: bool = True) -> dict:
    """استدعاء AI كملاذ أخير."""
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt_content = [_get_system_prompt()]
    
    if audio_path:
        myfile = genai.upload_file(audio_path)
        prompt_content.append(myfile)
    elif text_prompt:
        prompt_content.append(text_prompt)
    else:
        return None
    
    try:
        response = model.generate_content(prompt_content)
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw_text)
        
        validated = CommandResponse(**data)
        result = validated.model_dump()
        result['from_cache'] = False
        result['source'] = 'AI 🤖'
        
        if use_cache:
            transcription = result.get('transcription', text_prompt or '')
            command_cache.save_command(transcription, result['actions'], transcription)
        
        return result

    except Exception as e:
        st.error(f"❌ AI Error: {e}")
        return None

# ============================================
# SMART CONFIRMATION
# ============================================
def smart_confirmation(text: str) -> Optional[str]:
    """فهم التأكيد محلياً."""
    if not text:
        return None
    
    text_lower = text.lower().strip()
    
    yes_keywords = ['نعم', 'yes', 'نفذ', 'ok', 'موافق', 'تمام', 'اه', 'صح', 'ماشي']
    no_keywords = ['لا', 'no', 'إلغاء', 'cancel', 'stop', 'مش عايز']
    edit_keywords = ['عدل', 'edit', 'غير', 'change', 'بدل', 'مش كده']
    
    if any(word in text_lower for word in yes_keywords):
        return 'yes'
    if any(word in text_lower for word in no_keywords):
        return 'no'
    if any(word in text_lower for word in edit_keywords):
        return 'edit'
    
    return None

def parse_confirmation_command(audio_path: str = None, text: str = None) -> Optional[str]:
    if text:
        local_result = smart_confirmation(text)
        if local_result:
            return local_result
    
    if audio_path:
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            res = model.generate_content([
                "Reply: yes/no/edit",
                genai.upload_file(audio_path)
            ])
            txt = res.text.lower()
            if 'yes' in txt:
                return 'yes'
            if 'no' in txt:
                return 'no'
            if 'edit' in txt:
                return 'edit'
        except:
            pass
    
    return None

def analyze_confirmation(audio_path: str) -> str:
    return parse_confirmation_command(audio_path=audio_path) or "no"

# ============================================
# STATISTICS
# ============================================
def get_token_savings_stats() -> dict:
    """إحصائيات التوفير."""
    try:
        stats = command_cache.get_usage_stats()
        total_commands = stats['total_uses']
        cache_hits = total_commands - stats['unique']
        tokens_saved = cache_hits * 100
        cost_saved = (tokens_saved / 1_000_000) * 0.15
        
        return {
            'total_commands': total_commands,
            'unique_commands': stats['unique'],
            'cache_hits': cache_hits,
            'tokens_saved': tokens_saved,
            'money_saved_usd': cost_saved,
            'cache_hit_rate': (cache_hits / total_commands * 100) if total_commands > 0 else 0
        }
    except:
        return {
            'total_commands': 0,
            'unique_commands': 0,
            'cache_hits': 0,
            'tokens_saved': 0,
            'money_saved_usd': 0,
            'cache_hit_rate': 0
        }

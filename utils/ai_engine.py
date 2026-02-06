import os
import json
import re
import google.generativeai as genai
import streamlit as st
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import List, Optional, Literal
from . import command_cache

# ============================================
# 🧠 ENHANCED LOCAL PARSER
# ============================================

class EnhancedLocalParser:
    """معالج محلي ذكي - يعالج 70%+ من الأوامر بدون AI!"""
    
    def __init__(self):
        self.arabic_to_english = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
        self.last_video_duration = None
    
    def normalize_text(self, text: str) -> str:
        """تنقية وتوحيد النص."""
        text = text.translate(self.arabic_to_english)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه')
        text = re.sub(r'[!?،؛]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def parse_trim(self, text: str) -> Optional[dict]:
        """معالجة أوامر القص."""
        text = self.normalize_text(text.lower())
        
        # "قص من X إلى Y"
        patterns = [
            r'(من|from|start)\s*(\d+\.?\d*)\s*(إلى|to|until)\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*(إلى|to)\s*(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = [g for g in match.groups() if g and g[0].isdigit()]
                if len(groups) >= 2:
                    return {'action': 'trim', 'start': float(groups[0]), 'end': float(groups[1])}
        
        # "أول X ثواني"
        match = re.search(r'(أول|اول|first)\s*(\d+\.?\d*)', text)
        if match:
            return {'action': 'trim', 'start': 0, 'end': float(match.group(2))}
        
        # "آخر X ثواني"
        match = re.search(r'(آخر|اخر|last)\s*(\d+\.?\d*)', text)
        if match:
            duration = float(match.group(2))
            if self.last_video_duration:
                return {'action': 'trim', 'start': max(0, self.last_video_duration - duration), 'end': self.last_video_duration}
            return {'action': 'trim_last', 'duration': duration}
        
        return None
    
    def parse_speed(self, text: str) -> Optional[dict]:
        """معالجة أوامر السرعة."""
        text = self.normalize_text(text.lower())
        
        patterns = [
            r'(سرع|speed|fast)\s*(\d+\.?\d*)x?',
            r'x\s*(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = [g for g in match.groups() if g and g[0].isdigit()]
                if groups:
                    return {'action': 'speed', 'factor': min(float(groups[0]), 10.0)}
        
        if any(k in text for k in ['ضعف', 'double']):
            return {'action': 'speed', 'factor': 2.0}
        
        if any(k in text for k in ['بطيء', 'slow']):
            return {'action': 'speed', 'factor': 0.5}
        
        return None
    
    def parse_volume(self, text: str) -> Optional[dict]:
        """معالجة أوامر الصوت."""
        text = self.normalize_text(text.lower())
        
        match = re.search(r'(ارفع|increase)\s*(\d+)', text)
        if match:
            percent = float(match.group(2))
            return {'action': 'volume', 'level': min(1.0 + (percent / 100), 3.0)}
        
        match = re.search(r'(قلل|decrease)\s*(\d+)', text)
        if match:
            percent = float(match.group(2))
            return {'action': 'volume', 'level': max(1.0 - (percent / 100), 0.0)}
        
        if any(k in text for k in ['نص الصوت', 'half volume']):
            return {'action': 'volume', 'level': 0.5}
        
        if any(k in text for k in ['ضعف الصوت', 'double volume']):
            return {'action': 'volume', 'level': 2.0}
        
        return None
    
    def parse_crop(self, text: str) -> Optional[dict]:
        """معالجة أوامر القص."""
        text = text.lower()
        
        if any(k in text for k in ['9:16', 'ريلز', 'reels', 'shorts', 'tiktok']):
            return {'action': 'crop', 'aspect_ratio': '9:16'}
        
        if any(k in text for k in ['16:9', 'يوتيوب', 'youtube']):
            return {'action': 'crop', 'aspect_ratio': '16:9'}
        
        if any(k in text for k in ['1:1', 'مربع', 'square', 'post', 'instagram']):
            return {'action': 'crop', 'aspect_ratio': '1:1'}
        
        return None
    
    def parse_rotate(self, text: str) -> Optional[dict]:
        """معالجة أوامر التدوير."""
        text = text.lower()
        
        for angle in [90, 180, 270]:
            if str(angle) in text:
                return {'action': 'rotate', 'angle': angle}
        
        if any(k in text for k in ['دور يمين', 'rotate right']):
            return {'action': 'rotate', 'angle': 90}
        
        if any(k in text for k in ['دور شمال', 'rotate left']):
            return {'action': 'rotate', 'angle': -90}
        
        return None
    
    def parse_music(self, text: str) -> Optional[dict]:
        """كشف طلب موسيقى."""
        text = text.lower()
        
        if any(k in text for k in ['موسيقى', 'music', 'خلفيه', 'background']):
            match = re.search(r'(\d+)%', text)
            if match:
                return {'action': 'music', 'volume': min(float(match.group(1)) / 100, 1.0)}
            return {'action': 'music', 'volume': 0.3}
        
        return None
    
    def parse_multi_actions(self, text: str) -> List[dict]:
        """معالجة أوامر متعددة."""
        actions = []
        segments = re.split(r'\s+(و|ثم|and|then|\+)\s+', text)
        
        for segment in segments:
            if segment in ['و', 'ثم', 'and', 'then', '+']:
                continue
            
            for parser in [self.parse_trim, self.parse_speed, self.parse_crop, 
                          self.parse_rotate, self.parse_volume, self.parse_music]:
                result = parser(segment)
                if result:
                    actions.append(result)
                    break
            
            segment_lower = segment.lower()
            if any(k in segment_lower for k in ['كتم', 'mute']) and not any(a.get('action') == 'mute' for a in actions):
                actions.append({'action': 'mute'})
            
            if any(k in segment_lower for k in ['ابيض', 'اسود', 'bw', 'black', 'white']) and not any(a.get('action') == 'black_white' for a in actions):
                actions.append({'action': 'black_white'})
        
        return actions
    
    def parse(self, text: str, video_duration: float = None) -> Optional[dict]:
        """المعالج الرئيسي."""
        if not text or len(text.strip()) < 2:
            return None
        
        if video_duration:
            self.last_video_duration = video_duration
        
        multi_actions = self.parse_multi_actions(text)
        if multi_actions:
            return {
                'transcription': text,
                'actions': multi_actions,
                'source': 'local_parser 🚀',
                'from_cache': False,
                'tokens_saved': 150
            }
        
        return None

# ============================================
# ⚡ QUICK MATCH
# ============================================

QUICK_COMMANDS = {
    'اول 5 ثواني': [{'action': 'trim', 'start': 0, 'end': 5}],
    'اول 10 ثواني': [{'action': 'trim', 'start': 0, 'end': 10}],
    'اول 30 ثانيه': [{'action': 'trim', 'start': 0, 'end': 30}],
    'اول دقيقه': [{'action': 'trim', 'start': 0, 'end': 60}],
    'first 5 seconds': [{'action': 'trim', 'start': 0, 'end': 5}],
    'first 10 seconds': [{'action': 'trim', 'start': 0, 'end': 10}],
    'first 30 seconds': [{'action': 'trim', 'start': 0, 'end': 30}],
    'first minute': [{'action': 'trim', 'start': 0, 'end': 60}],
    
    'كتم الصوت': [{'action': 'mute'}],
    'شيل الصوت': [{'action': 'mute'}],
    'mute': [{'action': 'mute'}],
    'no sound': [{'action': 'mute'}],
    
    'ابيض واسود': [{'action': 'black_white'}],
    'black and white': [{'action': 'black_white'}],
    'bw': [{'action': 'black_white'}],
    
    'ريلز': [{'action': 'crop', 'aspect_ratio': '9:16'}],
    'reels': [{'action': 'crop', 'aspect_ratio': '9:16'}],
    'shorts': [{'action': 'crop', 'aspect_ratio': '9:16'}],
    'tiktok': [{'action': 'crop', 'aspect_ratio': '9:16'}],
    'يوتيوب شورتس': [{'action': 'crop', 'aspect_ratio': '9:16'}],
    
    'يوتيوب': [{'action': 'crop', 'aspect_ratio': '16:9'}],
    'youtube': [{'action': 'crop', 'aspect_ratio': '16:9'}],
    
    'انستجرام': [{'action': 'crop', 'aspect_ratio': '1:1'}],
    'instagram': [{'action': 'crop', 'aspect_ratio': '1:1'}],
    'square': [{'action': 'crop', 'aspect_ratio': '1:1'}],
    
    'سرع 2x': [{'action': 'speed', 'factor': 2.0}],
    'speed 2x': [{'action': 'speed', 'factor': 2.0}],
    '2x': [{'action': 'speed', 'factor': 2.0}],
    
    'بطيء': [{'action': 'speed', 'factor': 0.5}],
    'slow motion': [{'action': 'speed', 'factor': 0.5}],
    
    'دور 90': [{'action': 'rotate', 'angle': 90}],
    'rotate 90': [{'action': 'rotate', 'angle': 90}],
    
    'ريلز + كتم': [
        {'action': 'crop', 'aspect_ratio': '9:16'},
        {'action': 'mute'}
    ],
    'reels mute': [
        {'action': 'crop', 'aspect_ratio': '9:16'},
        {'action': 'mute'}
    ],
}

def quick_match(text: str) -> Optional[dict]:
    """تطابق فوري O(1)."""
    clean = text.lower().strip().replace('  ', ' ')
    
    if clean in QUICK_COMMANDS:
        return {
            'transcription': text,
            'actions': QUICK_COMMANDS[clean],
            'source': 'instant_match ⚡',
            'from_cache': False,
            'tokens_saved': 200
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
        raise ValueError("API Key not found")
    genai.configure(api_key=api_key)

def _get_system_prompt() -> str:
    return """Video editor. JSON only.
Actions: trim(start,end), mute(), volume(level), speed(factor), black_white(), rotate(angle), crop(aspect_ratio), music(volume), subtitle(text,start,end).
Output: {"transcription":"...","actions":[...]}"""

# ============================================
# HYBRID INTELLIGENCE
# ============================================

_parser = EnhancedLocalParser()

def analyze_command(
    audio_path: str = None, 
    text_prompt: str = None, 
    use_cache: bool = True, 
    cache_threshold: float = 0.85,
    video_duration: float = None
) -> dict:
    """
    نظام هجين 4-مستويات:
    1. Quick Match (⚡)
    2. Local Parser (🚀)
    3. Cache (💾)
    4. AI (🤖) - آخر حل
    """
    
    if audio_path:
        return _ai_fallback(audio_path, None, use_cache)
    
    if not text_prompt:
        return None
    
    # Level 1: Quick
    quick_result = quick_match(text_prompt)
    if quick_result:
        return quick_result
    
    # Level 2: Parser
    local_result = _parser.parse(text_prompt, video_duration)
    if local_result:
        if use_cache:
            command_cache.save_command(text_prompt, local_result['actions'], local_result['transcription'])
        return local_result
    
    # Level 3: Cache
    if use_cache:
        cached = command_cache.find_similar_command(text_prompt, threshold=cache_threshold)
        if cached:
            return {
                'transcription': cached['transcription'] or text_prompt,
                'actions': cached['actions'],
                'from_cache': True,
                'source': 'cache 💾',
                'similarity': cached['similarity'],
                'tokens_saved': 150
            }
    
    # Level 4: AI
    return _ai_fallback(None, text_prompt, use_cache)

def _ai_fallback(audio_path: str = None, text_prompt: str = None, use_cache: bool = True) -> dict:
    """استدعاء AI."""
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt_content = [_get_system_prompt()]
    
    if audio_path:
        prompt_content.append(genai.upload_file(audio_path))
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
        result['tokens_saved'] = 0
        
        if use_cache:
            command_cache.save_command(text_prompt or '', result['actions'], result.get('transcription', ''))
        
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
    
    if any(w in text_lower for w in ['نعم', 'yes', 'نفذ', 'ok', 'موافق', 'تمام']):
        return 'yes'
    if any(w in text_lower for w in ['لا', 'no', 'الغاء', 'cancel']):
        return 'no'
    if any(w in text_lower for w in ['عدل', 'edit', 'غير']):
        return 'edit'
    
    return None

def parse_confirmation_command(audio_path: str = None, text: str = None) -> Optional[str]:
    if text:
        return smart_confirmation(text)
    
    if audio_path:
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            res = model.generate_content(["yes/no/edit", genai.upload_file(audio_path)])
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

def get_ai_optimization_stats() -> dict:
    """إحصائيات التحسين."""
    try:
        stats = command_cache.get_usage_stats()
        total = stats['total_uses']
        unique = stats['unique']
        cache_hits = total - unique
        
        quick_est = int(total * 0.25)
        parser_est = int(total * 0.50)
        ai_est = total - (quick_est + parser_est + cache_hits)
        
        tokens_saved = (quick_est * 200) + (parser_est * 180) + (cache_hits * 150)
        money_saved = (tokens_saved / 1_000_000) * 0.15
        
        ai_percent = (ai_est / total * 100) if total > 0 else 0
        
        return {
            'total_commands': total,
            'quick_match': quick_est,
            'local_parser': parser_est,
            'cache': cache_hits,
            'ai': ai_est,
            'ai_percent': round(ai_percent, 2),
            'tokens_saved': tokens_saved,
            'money_saved_usd': round(money_saved, 4),
            'quick_commands_count': len(QUICK_COMMANDS),
        }
    except:
        return {
            'total_commands': 0,
            'ai_percent': 0,
            'tokens_saved': 0,
            'money_saved_usd': 0,
            'quick_commands_count': len(QUICK_COMMANDS),
        }

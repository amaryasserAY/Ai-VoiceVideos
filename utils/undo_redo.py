"""
نظام Undo/Redo: التراجع والإعادة للتعديلات.
"""
from typing import List, Dict, Optional

class UndoRedoManager:
    """مدير التراجع والإعادة."""
    
    def __init__(self):
        self.history: List[Dict] = []  # تاريخ التعديلات
        self.current_index: int = -1   # المؤشر الحالي
    
    def add_state(self, video_path: str, actions: List[Dict], music_path: str = None):
        """إضافة حالة جديدة للتاريخ."""
        # حذف أي حالات بعد المؤشر الحالي (عند عمل Redo ثم إضافة جديد)
        self.history = self.history[:self.current_index + 1]
        
        # إضافة الحالة الجديدة
        self.history.append({
            'video_path': video_path,
            'actions': actions.copy() if actions else [],
            'music_path': music_path
        })
        self.current_index = len(self.history) - 1
    
    def undo(self) -> Optional[Dict]:
        """التراجع خطوة واحدة."""
        if self.can_undo():
            self.current_index -= 1
            return self.history[self.current_index].copy()
        return None
    
    def redo(self) -> Optional[Dict]:
        """الإعادة خطوة واحدة."""
        if self.can_redo():
            self.current_index += 1
            return self.history[self.current_index].copy()
        return None
    
    def can_undo(self) -> bool:
        """هل يمكن التراجع؟"""
        return self.current_index > 0
    
    def can_redo(self) -> bool:
        """هل يمكن الإعادة؟"""
        return self.current_index < len(self.history) - 1
    
    def get_current(self) -> Optional[Dict]:
        """الحصول على الحالة الحالية."""
        if 0 <= self.current_index < len(self.history):
            return self.history[self.current_index].copy()
        return None
    
    def clear(self):
        """مسح التاريخ."""
        self.history = []
        self.current_index = -1

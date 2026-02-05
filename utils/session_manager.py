"""
إدارة مشاريع Sessions: حفظ/فتح مشاريع كاملة.
"""
import os
import json
import sqlite3
from typing import Optional, Dict, List
from datetime import datetime
from .config import DB_SESSIONS_PATH

DB_PATH = str(DB_SESSIONS_PATH)

def init_database():
    """إنشاء قاعدة بيانات Sessions."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            video_path TEXT,
            actions_json TEXT NOT NULL,
            music_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def save_session(name: str, video_path: str, actions: List[Dict], music_path: str = None) -> bool:
    """حفظ جلسة جديدة."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        actions_json = json.dumps(actions, ensure_ascii=False)
        cursor.execute("""
            INSERT INTO sessions (name, video_path, actions_json, music_path)
            VALUES (?, ?, ?, ?)
        """, (name, video_path, actions_json, music_path))
        conn.commit()
        return True
    except Exception as e:
        print(f"Save session error: {e}")
        return False
    finally:
        conn.close()

def load_session(session_id: int) -> Optional[Dict]:
    """تحميل جلسة من ID."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name, video_path, actions_json, music_path FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': session_id,
                'name': row[0],
                'video_path': row[1],
                'actions': json.loads(row[2]),
                'music_path': row[3]
            }
    except Exception as e:
        print(f"Load session error: {e}")
    finally:
        conn.close()
    return None

def list_sessions() -> List[Dict]:
    """قائمة بكل الجلسات المحفوظة."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, name, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return [
            {
                'id': r[0],
                'name': r[1],
                'created_at': r[2],
                'updated_at': r[3]
            }
            for r in rows
        ]
    except Exception as e:
        print(f"List sessions error: {e}")
        return []
    finally:
        conn.close()

def delete_session(session_id: int) -> bool:
    """حذف جلسة."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Delete session error: {e}")
        return False
    finally:
        conn.close()

def export_session(session_id: int) -> Optional[str]:
    """تصدير جلسة كـ JSON."""
    session = load_session(session_id)
    if session:
        return json.dumps(session, indent=2, ensure_ascii=False)
    return None

def import_session(json_str: str) -> bool:
    """استيراد جلسة من JSON."""
    try:
        data = json.loads(json_str)
        return save_session(
            data.get('name', 'Imported Session'),
            data.get('video_path', ''),
            data.get('actions', []),
            data.get('music_path')
        )
    except Exception as e:
        print(f"Import session error: {e}")
        return False

init_database()

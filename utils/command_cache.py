"""
نظام ذكي لحفظ الأوامر الشائعة وتوفير التوكينز.
يحفظ الأوامر + JSON المقابل في SQLite للرجوع السريع بدون AI.
"""
import sqlite3
import json
import os
from typing import Optional, Dict, List
from difflib import SequenceMatcher
from .config import DB_CACHE_PATH

DB_PATH = str(DB_CACHE_PATH)

def init_database():
    """إنشاء قاعدة البيانات إذا لم تكن موجودة."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # جدول الأوامر المحفوظة (Cache)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command_text TEXT NOT NULL,
            command_hash TEXT UNIQUE,
            actions_json TEXT NOT NULL,
            transcription TEXT,
            usage_count INTEGER DEFAULT 1,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # جدول القوالب (Templates) - الجديد
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            actions_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# --- دوال الكاش والأوامر (كما هي) ---
def _hash_command(text: str) -> str:
    import hashlib
    normalized = text.lower().strip()
    return hashlib.md5(normalized.encode()).hexdigest()

def _similarity(text1: str, text2: str) -> float:
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def save_command(command_text: str, actions: List[Dict], transcription: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cmd_hash = _hash_command(command_text)
    actions_json = json.dumps(actions, ensure_ascii=False)
    try:
        cursor.execute("INSERT INTO commands (command_text, command_hash, actions_json, transcription) VALUES (?, ?, ?, ?)", 
                       (command_text, cmd_hash, actions_json, transcription))
        conn.commit()
    except sqlite3.IntegrityError:
        cursor.execute("UPDATE commands SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP WHERE command_hash = ?", (cmd_hash,))
        conn.commit()
    finally:
        conn.close()

def find_similar_command(command_text: str, threshold: float = 0.85) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT command_text, actions_json, transcription, usage_count FROM commands")
    rows = cursor.fetchall()
    conn.close()
    best_match = None
    best_score = 0
    for row in rows:
        saved_text, actions_json, transcription, usage_count = row
        score = _similarity(command_text, saved_text)
        if score > best_score:
            best_score = score
            if score >= threshold:
                best_match = {'command_text': saved_text, 'actions': json.loads(actions_json), 'transcription': transcription, 'similarity': score, 'usage_count': usage_count}
    return best_match

def get_usage_stats() -> dict:
    init_database()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM commands")
        unique_cmds = c.fetchone()[0] or 0
        c.execute("SELECT SUM(usage_count) FROM commands")
        total_hits = c.fetchone()[0] or 0
        tokens_saved = (total_hits - unique_cmds) * 50
        if tokens_saved < 0: tokens_saved = 0
        return {"unique": unique_cmds, "total_uses": total_hits, "saved_tokens": tokens_saved}
    except:
        return {"unique": 0, "total_uses": 0, "saved_tokens": 0}
    finally:
        conn.close()

def get_popular_commands(limit: int = 10) -> List[Dict]:
    """جلب الأوامر الأكثر استخداماً."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT command_text, actions_json, usage_count
        FROM commands ORDER BY usage_count DESC, last_used DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    out = []
    for row in rows:
        try:
            out.append({"command": row[0], "actions": json.loads(row[1]), "usage_count": row[2]})
        except (json.JSONDecodeError, TypeError):
            continue
    return out

def clear_cache():
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    init_database()

def export_db_to_json() -> str:
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT command_text, actions_json, transcription, usage_count FROM commands")
    rows = cursor.fetchall()
    conn.close()
    data = []
    for row in rows:
        data.append({"command_text": row[0], "actions": json.loads(row[1]), "transcription": row[2], "usage_count": row[3]})
    return json.dumps(data, indent=2, ensure_ascii=False)

def import_db_from_json(json_str: str) -> int:
    try:
        data = json.loads(json_str)
        count = 0
        for item in data:
            if "command_text" in item and "actions" in item:
                save_command(item["command_text"], item["actions"], item.get("transcription"))
                count += 1
        return count
    except: return 0

# --- دوال القوالب (Templates) - الجديد ---
def save_template(name: str, actions: List[Dict], description: str = ""):
    """حفظ مجموعة خطوات كقالب."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    actions_json = json.dumps(actions, ensure_ascii=False)
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO templates (name, description, actions_json)
            VALUES (?, ?, ?)
        """, (name, description, actions_json))
        conn.commit()
        return True
    except Exception as e:
        print(f"Template Error: {e}")
        return False
    finally:
        conn.close()

def get_all_templates() -> List[Dict]:
    """جلب كل القوالب المحفوظة."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, actions_json FROM templates ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{'name': r[0], 'description': r[1], 'actions': json.loads(r[2])} for r in rows]

def delete_template(name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM templates WHERE name = ?", (name,))
    conn.commit()
    conn.close()

init_database()
"""
记忆层 - 持久化存储
"""
import sqlite3
from typing import Dict, Any, List, Optional
import json


class MemoryStore:
    """SQLite 记忆存储"""
    
    def __init__(self, db_path: str = "novel_agent.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.init_tables()
    
    def init_tables(self):
        """初始化表结构"""
        cursor = self.conn.cursor()
        
        # 小说表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS novels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                genre TEXT,
                outline TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 角色表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER,
                name TEXT,
                role TEXT,
                psychology TEXT,
                behavior TEXT,
                relationships TEXT,
                FOREIGN KEY (novel_id) REFERENCES novels(id)
            )
        """)
        
        # 章节表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER,
                chapter_num INTEGER,
                content TEXT,
                status TEXT,
                review_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (novel_id) REFERENCES novels(id)
            )
        """)
        
        # 伏笔表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS foreshadowing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER,
                fs_type TEXT,
                description TEXT,
                importance INTEGER,
                plant_chapter INTEGER,
                reveal_chapter INTEGER,
                status TEXT,
                FOREIGN KEY (novel_id) REFERENCES novels(id)
            )
        """)
        
        self.conn.commit()
    
    def save_novel(self, novel: Dict[str, Any]) -> int:
        """保存小说"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO novels (title, genre, outline, status) VALUES (?, ?, ?, ?)",
            (novel.get("title"), novel.get("genre"), 
             json.dumps(novel.get("outline", {}), ensure_ascii=False),
             novel.get("status", "planning"))
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def save_character(self, novel_id: int, character: Dict[str, Any]):
        """保存角色"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO characters (novel_id, name, role, psychology, behavior, relationships) VALUES (?, ?, ?, ?, ?, ?)",
            (novel_id, character.get("name"), character.get("role"),
             json.dumps(character.get("psychology", {}), ensure_ascii=False),
             json.dumps(character.get("behavior", {}), ensure_ascii=False),
             json.dumps(character.get("relationships", []), ensure_ascii=False))
        )
        self.conn.commit()
    
    def save_chapter(self, novel_id: int, chapter_num: int, content: str):
        """保存章节"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO chapters (novel_id, chapter_num, content, status) VALUES (?, ?, ?, ?)",
            (novel_id, chapter_num, content, "draft")
        )
        self.conn.commit()
    
    def get_novel(self, novel_id: int) -> Optional[Dict[str, Any]]:
        """获取小说"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM novels WHERE id = ?", (novel_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "title": row[1],
                "genre": row[2],
                "outline": json.loads(row[3]),
                "status": row[4]
            }
        return None
    
    def get_characters(self, novel_id: int) -> List[Dict[str, Any]]:
        """获取角色列表"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM characters WHERE novel_id = ?", (novel_id,))
        rows = cursor.fetchall()
        return [{"id": r[0], "name": r[2], "role": r[3]} for r in rows]
    
    def close(self):
        """关闭连接"""
        self.conn.close()
